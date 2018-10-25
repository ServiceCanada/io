#!/usr/bin/env perl
use common::sense;

use Env;
use File::Spec;
use lib File::Spec->catdir( substr( $DOCUMENT_ROOT, 0, rindex( $DOCUMENT_ROOT, '/')  ), 'cgi-lib');

use cPanelUserConfig;
use Path::Tiny qw/path/;

use YAML::Tiny;
use Text::CSV_XS;
use Mustache::Simple;

use DBI;
use CGI qw(-utf8);

use Text::Markdown 'markdown';
use Data::Dumper;

# =================
# = PREPROCESSING =
# =================
my $dir = path($0)->realpath;
my $base = path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ) );
my $config = YAML::Tiny->read( $dir->sibling('index.yml')->stringify )->[0];
my $stache = Mustache::Simple->new();

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$base->child( $config->{'database'}->{'path'} )
    ,"","",{ sqlite_unicode => 1 }
);

my $cgi = CGI->new();

my ( $template, $lang, $io ) = (
    $cgi->param('template'),
    $cgi->param('language'),
    path( $cgi->tmpFileName( $cgi->param('input-file') ) )->openr
);

print $cgi->header("text/html;charset=UTF-8");

$template = $dir->sibling('.templates')->child( $template.'.tmpl' )->realpath;


if ( ! $template->is_file or $dir->subsumes( $template ) )
{
    print "Opps not template";
    exit();
}

my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                or die "Cannot use CSV: ".Text::CSV->error_diag ();

$csv->column_names( map { sanitize( $_ ) } @{ $csv->getline($io) } );

my $mold = $template->slurp_utf8;

my $rendered = "";

while (my $row = $csv->getline_hr($io) )
{
    $row->{'Anticipated'} = ( $lang eq 'en' ) ? "Result anticipated" : "Résultat obtenu";
    $row->{'ClickForMore'} = ( $lang eq 'en' ) ? "Click to see more information" : "Cliquez pour voir plus d'informations";
    $row->{'MoreInformation'} = ( $lang eq 'en' ) ? "More Information" : "Plus d'information";
    $row->{'Label'} = label( $row->{'Status'} );
    $row->{'MinList'} = ministers( $row->{'Ministers'} );
    # MarkDown for Comment
    $row->{'Comment'} = compress( markdown( normalize( $row->{'Comment'} ) ) );
    # Other Links
    $row->{'OtherLinks'} = otherlinks( 
            [ $row->{'Link_1'}, $row->{'Link_Text_1'} ],
            [ $row->{'Link_2'}, $row->{'Link_Text_2'} ],
            [ $row->{'Link_3'}, $row->{'Link_Text_3'} ],
            [ $row->{'Link_4'}, $row->{'Link_Text_4'} ],
            [ $row->{'Link_5'}, $row->{'Link_Text_5'} ]
    );
    

    $rendered .= $stache->render( $mold, $row );
}

print $stache->render( $dir->sibling('complete.html')->slurp_utf8, { rendered => $rendered } );

# ============
# = RESPONSE =
# ============




sub ministers 
{ 
    my ( $ministers ) = @_; 
    my $list = ( $lang eq 'en' ) ? '<p>Mandate letters that include this commitment:</p>' : '<p>Lettres de mandat qui incluent cet engagement :</p>'; 
    $list .= "\n<ul>\n"; 
    foreach my $minister ( split /;/, $ministers ) 
    { 
        my $min =  $dbh->selectrow_hashref('SELECT * FROM ministers WHERE title LIKE\'%'.$minister.'%\' LIMIT 1');
        next unless $min->{title};
        $list .= "<li><a href=\"$min->{link}\">$min->{title}</a></li>\n"; 
    } 

    return $list."</ul>\n"; 
} 



sub label 
{ 
    my $tag = shift; 
    return "<span class=\"label label-success completed-fully-met\">$tag</span>" if ( $tag =~ /(fully met|totalement)$/ ); 
    return "<span class=\"label label-success completed-modified\">$tag</span>" if ( $tag =~ /(modified|modifié)$/ ); 
    return "<span class=\"label label-success underway-on-track\">$tag</span>" if ( $tag =~ /(on track|en voie)$/ ); 
    return "<span class=\"label label-success underway-with-challenges\">$tag</span>" if ( $tag =~ /(with challenges|avec défis)$/ ); 
    return "<span class=\"label label-success not-being-pursued\">$tag</span>" if ( $tag =~ /(pursued|envisagé)$/ ); 
    return "<span class=\"label label-success guidance\">$tag</span>" if ( $tag =~ /(commitment|permanent)$/ ); 
} 

sub otherlinks 
{ 
    my ($list, $has, @links) = ( "<ul>\n", 0, @_ ); 
    
    
    foreach my $link ( @links ) 
    { 
        next unless ( $link->[1] );
        $list .= "<li><a href=\"".$link->[0]."\">".$link->[1]."</a></li>\n";
        $has = 1;
    } 
    
    return ( $has ) ? $list."</ul>\n" : undef ; 
}

sub compress {
    my ( $text ) = @_;
    $text =~ s/[\n\r]+/<br \/>\n/g;
    $text =~ s/<\/p><br \/>/<\/p>/g;
    return $text;
}

sub normalize
{
    my ( $text ) = @_;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    return $text;
}

#FUNCTIONS
sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    return $text;
}
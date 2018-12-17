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
use Text::StripAccents;

# =================
# = PREPROCESSING =
# =================

my $dir = path($0)->realpath;
my $base = path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ) );

my $config = YAML::Tiny->read( $dir->sibling('index.yml')->stringify )->[0];
my $stache = Mustache::Simple->new();
my $scharacter = quotemeta('_x000D_');

my %tems;

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
    next unless ( $row->{'Comment'} );
    
    if ( $lang ne 'en' )
    {
        $row->{'FrenchSpace'} = "&nbsp;"
    } 
    
    $row->{'Anticipated'} = ( $lang eq 'en' ) 
                    ? "Result ".( ($row->{'Status'} =~ /^(Completed|Complété)/ ) ? "achieved" : "anticipated" )
                    : "Résultat ".( ($row->{'Status'} =~ /^(Completed|Complété)/ ) ? "obtenu" : "escompté" );

    $row->{'ClickForMore'} = ( $lang eq 'en' ) ? "Click to see more information" : "Cliquez pour voir plus d'informations";
    $row->{'MoreInformation'} = ( $lang eq 'en' ) ? "More Information" : "Plus d'information";
    $row->{'Label'} = label( $row->{'Status'}, $lang );
    $row->{'MinList'} = ministers( $row->{'Ministers'} );

    # MarkDown for Comment & Commitment
    $row->{'Comment'} = compress( markdown( normalize( $row->{'Comment'} ) ) );
    $row->{'Commitment'} = markdown( $row->{'Commitment'} );
    $row->{'sStatement'} = stripMarkdown( $row->{'Statement'} );
    $row->{'Statement'} = markdown( $row->{'Statement'} );
    # Other Links
    $row->{'OtherLinks'} = otherlinks( 
            [ $row->{'Link_1'}, $row->{'Link_Text_1'} ],
            [ $row->{'Link_2'}, $row->{'Link_Text_2'} ],
            [ $row->{'Link_3'}, $row->{'Link_Text_3'} ],
            [ $row->{'Link_4'}, $row->{'Link_Text_4'} ],
            [ $row->{'Link_5'}, $row->{'Link_Text_5'} ]
    );
    
    $row->{'Vintage'} = $config->{'datemap'}->{ $row->{'Vintage'} }->{ $lang };
    
    $row->{'Status'} = modify( $row->{'Status'} );

    $rendered .= $stache->render( $mold, $row );
}

# ============
# = RESPONSE =
# ============
print $stache->render( $dir->sibling('complete.html')->slurp_utf8, { rendered => $rendered } );

# ====================
# = HELPER FUNCTIONS =
# ====================
sub ministers 
{ 
    my ( $ministers ) = @_; 
    my $list = ( $lang eq 'en' ) ? '<p>Mandate letters that include this commitment:</p>' : '<p>Lettres de mandat qui incluent cet engagement :</p>'; 
    $list .= "\n<ul>\n"; 
    foreach my $minister ( split /;/, $ministers ) 
    { 
        my ($link, $title) =  $dbh->selectrow_array('SELECT link, title FROM ministers WHERE id = ? LIMIT 1', {}, generate( $minister ) );
        $list .= "<li><a href=\"$link\">$title</a></li>\n"; 
    } 

    return $list."</ul>\n"; 
}

sub modify 
{ 
    my ($tag ) = @_;
    
    $tag = cleanse( $tag );
    
    if ( slugify( $tag ) =~ /^(actions-taken-progress-made|actions-prises-progres-accomplis)$/ )
    {
        $tag .= '&#8203;';
    }
    
    return $tag;
    
}

sub label 
{ 
    my ($tag, $lang) = @_;
    
    my $slug = slugify( $tag );
    
    $tag = cleanse( $tag );
    
    if ( $slug =~ /^(actions-taken-progress-made|actions-prises-progres-accomplis)$/ )
    {
         return "<span class=\"label label-success underway-on-track\" style=\"background: #d0e6d0;border-color: #92c691;\">$tag</span>"
    }   
    
    if ( $slug =~ /^(actions-taken-progress-made-toward-ongoing-goal|actions-prises-progres-accomplis-vers-un-objectif-permanent)$/ )
    {
         return "<span class=\"label label-success guidance\"  style=\"background: #d0e6d0;border-color: #b6d9b6;\">$tag</span>"
    }

     if ( $slug =~ /^(actions-taken-progress-made-facing-challenges|actions-prises-progres-accomplis-defis-a-relever)$/ )
    {
         return "<span class=\"label label-success underway-with-challenges\" style=\"background: rgba(246,96,2,0.1);border-color: #f66002;\">$tag</span>"
    }
    
    if ( $slug =~ /^(completed-fully-met|complete-totalement)$/ )
    {
        return "<span class=\"label label-success completed-fully-met\" style=\"background: #d0e6d0;border-color: #478e46;\">$tag</span>"; 
    }
    
    if ( $slug =~ /^(completed-modified|complete-modifie)$/ )
    {
        return "<span class=\"label label-success completed-modified\" style=\"background: #d0e6d0;border-color: #65aa65;\">$tag</span>";  
    }
    
    return "<span class=\"label label-success not-being-pursued\" style=\"background: rgba(231,0,0,0.1);border-color: #e70000;\">$tag</span>"; 
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

sub cleanse
{
    my ( $text ) = @_;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    $text =~ s/\n+/ /gs;
    $text =~ s/\s+/ /g;
    return $text;
}

sub normalize
{
    my ( $text ) = @_;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    $text =~s/$scharacter//g;
    return $text;
}
#FUNCTIONS
sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    $text =~ s/$scharacter//g;
    return $text;
}

sub stripMarkdown
{
    my ( $text ) = @_;
    $text =~ s/\*//g;
    $text =~ s/_//g;
    $text =~ s/\+//g;
    return $text;
}

sub slugify
{
    my ( $text ) = @_;
    $text = normalize( $text );
    # remove accents
    $text = stripaccents( $text );
    $text =~ s/[^a-z0-9]+/-/gi;
    $text =~ s/[-]+/-/g;
    return lc($text); 
}

sub generate
{
    my ( $text ) = @_;
    $text = stripaccents($text);
    $text =~ s/[^a-z]//gi;
    return lc($text);
}
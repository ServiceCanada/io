#!/Users/masterbee/perl5/perlbrew/perls/perl-5.16.3/bin/perl
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
use CGI;

use Text::Markdown;
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
    ,"",""
);

my $cgi = CGI->new();

my ( $template, $io ) = (
    $cgi->param('template'),
    path( $cgi->tmpFileName( $cgi->param('input-file') ) )->openr_raw
);

print $cgi->header;

$template = $dir->sibling('.templates')->child( $template.'.tmpl' )->realpath;


if ( ! $template->is_file or $dir->subsumes($template) )
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
    $row->{'Label'} = label( $row->{'Status'} );
    $row->{'MinList'} = ministers( $row->{'Ministers'} );
    $rendered .= $stache->render( $mold, $row );
}

print $stache->render( $dir->sibling('complete.html')->slurp_utf8, { rendered => $rendered } );

# ============
# = RESPONSE =
# ============




sub ministers 
{ 
    my ( $ministers, $lang ) = @_; 
    my $list = ( $lang eq 'en' ) ? '<p>Mandate letters that include this commitment:</p>' : '<p>Lettres de mandat qui incluent cet engagement :</p>'; 
    $list .= "<ul>"; 
    foreach my $minister ( split /;/, $ministers ) 
    { 
        my $min =  $dbh->selectrow_hashref('SELECT * FROM ministers WHERE title=\''.$minister.'\' LIMIT 1');
        $list .= "<li><a href=\"$min->{link}\">$min->{title}</a></li>"; 
    } 

    return $list."</ul>"; 
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


#FUNCTIONS
sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    return $text;
}
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
use HTML::Entities;

use Text::Markdown 'markdown';
use Text::StripAccents;

# =================
# = PREPROCESSING =
# =================

my $dir = path($0)->realpath;
my $base = path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ) );

my $config = YAML::Tiny->read( $dir->sibling('index.yml')->stringify )->[0];
my $stache = Mustache::Simple->new();

my $rolodex = $config->{'subjects'};

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
    next unless ( $row->{'owner_org'} );

    my $dataset = {
        start_date => $row->{'start_date'},
        end_date => $row->{'end_date'},
        status => $row->{'status'},
        subjects => $row->{'subjects'},
        subject => extroplate( $row->{'subjects'}, $lang ),
        title => ( $lang eq 'en' )  ? $row->{'title_en'} : $row->{'title_fr'},
        description => ( $lang eq 'en' )  ? $row->{'description_en'} : $row->{'description_fr'},
        owner => splitselect( '\s+\|\s+', $row->{'owner_org_title'}, $lang )
    };

    if ( begins_with( $row->{'profile_page_en'}, 'http' ) )
    {
        $dataset->{'link'} = ( $row->{'profile_en'} )  ? $row->{'profile_page_en'} : $row->{'profile_page_fr'};
    }

    $rendered .= $stache->render( $mold, $dataset );
}

# ============
# = RESPONSE =
# ============
print $stache->render( $dir->sibling('complete.html')->slurp_utf8, { rendered => $rendered } );

# ====================
# = HELPER FUNCTIONS =
# ====================
sub extroplate 
{     
    my ($text, $lang) = @_;
    my @subjects = split( /,/, $text );
    for ( my $idx = 0; $idx < scalar(@subjects); $idx++ )
    {
       #my ( $label ) = $dbh->selectrow_array( 'SELECT '.$lang.' FROM subjects WHERE id = ?', {}, $subjects[$idx] );
       $subjects[$idx] = $rolodex->{ $subjects[$idx] }->{$lang};
    }
    return join( ' | ', @subjects );
}

sub toiso
{
    my @date = split( /\//, shift );
   return sprintf "%04d-%02d-%02d", reverse @date;
}

sub splitselect
{
    my ($sep, $text, $lang ) = @_;
    my @choices = split( /$sep/, $text );
    return ( $lang eq 'en' ) ? $choices[0] : $choices[1];
}

sub normalize
{
    my ( $text ) = @_;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    return $text;
}

sub compress
{
    my ( $text ) = @_;
    $text =~ s/\R//g;
     $text =~ s/\s+/ /g;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    return $text;
}

sub begins_with
{
    return substr($_[0], 0, length($_[1])) eq $_[1];
}

#FUNCTIONS
sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    return $text;
}

sub generate
{
    my ( $text ) = @_;
    $text = stripaccents($text);
    $text =~ s/[^a-z]//gi;
    return lc($text);
}
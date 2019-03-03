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

use CGI qw(-utf8);

use Text::StripAccents;

# =================
# = PREPROCESSING =
# =================

my $dir = path($0)->realpath;
my $base = path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ) );

my $stache = Mustache::Simple->new();
my $scharacter = quotemeta('_x000D_');

my $cgi = CGI->new();

my ( $io, $mins ) = (
    path( $cgi->tmpFileName( $cgi->param('input-file') ) ),
    {}
);

print $cgi->header("text/html;charset=UTF-8");

my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                or die "Cannot use CSV: ".Text::CSV->error_diag ();

my @ministers = $io->lines( { chomp => 1, binmode => ':raw' });

shift(@ministers); # we do not want the headers

foreach my $minister (@ministers)
{
    my $status = $csv->parse($minister);
    my @columns = $csv->fields();

    next if ( $columns[0] !~ /\S/ || $columns[2] !~ /\S/  );
    # English
    $mins->{ slugify( $columns[0] ) } = {
        'title' => $columns[0],
        'link' => $columns[1],
    };

    # French
    $mins->{ slugify( $columns[2] ) } = {
        'title' => $columns[2],
        'link' => $columns[3],
    };
}


# ============
# = RESPONSE =
# ============
print $stache->render( $dir->sibling('complete.html')->slurp_utf8, { rendered => YAML::Tiny->Dump( { ministers => $mins } ) } );

# ====================
# = HELPER FUNCTIONS =
# ====================

sub normalize
{
    my ( $text ) = @_;
    $text =~ s/^\s+//;
    $text =~ s/\s+$//;
    $text =~s/$scharacter//g;
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

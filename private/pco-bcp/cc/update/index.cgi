#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use DBI;
use SQL::Maker;
use YAML::Tiny;
use Text::CSV_XS;

# =================
# = PREPROCESSING =
# =================

my ( $base, $config, $builder ) = (
    path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/private/' ) ) ),
    YAML::Tiny->read( path($0)->sibling('index.yml')->stringify )->[0],
    SQL::Maker->new( driver => 'SQLite' )
);

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$base->child($config->{'database'}->{'path'})
    ,"",""
);

my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                or die "Cannot use CSV: ".Text::CSV->error_diag ();
                
                
my @subjects = path($0)->sibling('dataset.csv')->lines( { chomp => 1, binmode => ':raw' });

shift(@subjects); # we do not want the headers
                
foreach my $subject (@subjects)
{
    my $status = $csv->parse($subject);
    my @columns = $csv->fields();
    my $values = {
        'id' => $columns[0],
        'en' => $columns[1],
        'fr' => $columns[2]
    };
    my ($stmt, @bind) = $builder->insert( 'subjects', $values );
    my $sth = $dbh->prepare($stmt);
    $sth->execute(@bind);
    
}
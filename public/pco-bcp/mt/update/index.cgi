#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use DBI;
use SQL::Maker;
use YAML::Tiny;
use Text::CSV_XS;
use Storable;

# =================
# = PREPROCESSING =
# =================

my ( $base, $config, $builder ) = (
    path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ) ),
    YAML::Tiny->read( path($0)->sibling('index.yml')->stringify )->[0],
    SQL::Maker->new( driver => 'SQLite' )
);

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$base->child($config->{'database'}->{'path'})
    ,"",""
);

my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                or die "Cannot use CSV: ".Text::CSV->error_diag ();
                
                
my @ministers = path($0)->sibling('ministers.csv')->lines( { chomp => 1, binmode => ':raw' });

shift(@ministers); # we do not want the headers
                
foreach my $minister (@ministers)
{
    my $status = $csv->parse($minister);
    my @columns = $csv->fields();
    my $values = {
        'title' => $columns[0],
        'link' => $columns[1],
    };
    my ($stmt, @bind) = $builder->insert( 'ministers', $values );
    my $sth = $dbh->prepare($stmt);
    $sth->execute(@bind);
    
    my $values = {
        'title' => $columns[2],
        'link' => $columns[3],
    };
    ($stmt, @bind) = $builder->insert( 'ministers', $values );
    $sth = $dbh->prepare($stmt);
    $sth->execute(@bind);
    
}
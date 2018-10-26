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
use Text::StripAccents;

# =================
# = PREPROCESSING =
# =================

my ( $base, $config, $builder) = (
    path( substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ) ),
    YAML::Tiny->read( path($0)->sibling('index.yml')->stringify )->[0]
);

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$base->child($config->{'database'}->{'path'})
    ,"",""
);

my $add = $dbh->prepare('INSERT INTO ministers (id, title, link) VALUES (?, ?, ?)');

print "[starting] loading ministers\n";

my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                or die "Cannot use CSV: ".Text::CSV->error_diag ();
                        
my $io = path($0)->sibling('ministers.csv')->openr;

$csv->column_names( map { sanitize( $_ ) } @{ $csv->getline($io) } );

while (my $row = $csv->getline_hr($io) )
{   
    next unless ( $row->{'link'} =~ /[a-zA-Z]/ );
    
    if ( my ($id, $title) = $dbh->selectrow_array( "SELECT id , title FROM ministers WHERE id = ? LIMIT 1" , {}, generate( $row->{'title'} ) ) )
    {
        print "Ok we have a duplicate $title\n";
        next;
    }
    # english
    $add->execute( generate( $row->{'title'} ), $row->{'title'}, $row->{'link'} );
    
    if ( my ( $id, $title ) = $dbh->selectrow_array( "SELECT id , title FROM ministers WHERE id = ? LIMIT 1" , {}, generate( $row->{'titre'} ) ) )
    {
        print "Ok we have a duplicate $title\n";
        next;
    }
    # french 
    $add->execute( generate( $row->{'titre'} ), $row->{'titre'}, $row->{'lien'} );
    
}

print "[complete] OK...";
               
#FUNCTIONS
sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    return lc($text);
}

sub generate
{
    my ( $text ) = @_;
    $text = stripaccents($text);
    $text =~ s/[^a-z]//gi;
    return lc($text);
}
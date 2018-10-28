#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Storable qw/dclone/; 
use Path::Tiny qw/path/;

use Prism;
use DBI;
use YAML::Tiny;
use Text::CSV_XS;

use Data::Dmp qw/dd/;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1 }
);

my $add = $dbh->prepare('INSERT INTO recalls ( id, title, abstract, date, lang, parent, category, subcategory, url ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
my $update = $dbh->prepare('UPDATE recalls SET title = ?, subcategory = ? WHERE id = ?');

while ( my $resource = $prism->next() )
{
    my $io = $prism->download( $resource->{'uri'}, $resource->{'source'} );
    
    my $idx = 1;
    
    if ( $io == undef )
    {
        $io = $prism->parent->child( $resource->{'source'} );
    }
    
    $io = $io->openr;
    
    my $csv = Text::CSV_XS->new ( { binary => 1 } )  # should set binary attribute.
                    or die "Cannot use CSV: ".Text::CSV->error_diag ();
                    
    $csv->column_names( map { sanitize( $_ ) } @{ $csv->getline($io) } );
    
    while (my $row = $csv->getline_hr($io) )
    {
        my $rez = dclone( $resource );
        my $dataset = $prism->transform( $row, $rez );
        
        # lets check if this recall exists
        if ( my ( $id, $sub, $title ) = $dbh->selectrow_array("SELECT id, subcategory, title  FROM recalls WHERE id=? AND lang=? LIMIT 1", {}, $dataset->{'id'}, $dataset->{'lang'} ) )
        {
            unless ( $sub =~ m/\b$dataset->{'subcategory'}\b/ )
            {
                # We are merging here
                print " [merging] [$dataset->{lang}] (".$idx++." / ~ 120000) ".$dataset->{url}."\n";
                
                $title .= ', ' . $dataset->{'subcategory'} unless $title =~ m/\b$dataset->{'subcategory'}\b/;
                $sub .= ';' . $dataset->{'subcategory'};
                $update->execute( $title, $sub, $id );
            }
            next;
        }
        
        $add->execute( map { $dataset->{$_} }  qw/id title abstract date lang parent category subcategory url/ );
        print " [added] [$dataset->{lang}] (".$idx++." / ~ 120000) ".$dataset->{url}."\n";
    }
    
}

print "[complete] OK";



sub sanitize
{
    my ( $text ) = @_;
    $text =~ s/\n+//g;
    $text =~ s/\s+/_/g;
    return $text;
}
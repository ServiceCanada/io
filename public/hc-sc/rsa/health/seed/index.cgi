#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use Prism;
use DBI;
use JSON;
use Storable qw/dclone/; 
use Data::Dumper;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1 }
);

my $coder = JSON->new->utf8;

my $add = $dbh->prepare('INSERT INTO recalls ( id, title, abstract, date, lang, parent, category, subcategory, url ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');


while (my $resource = $prism->next() )
{
    my $io = $coder->decode( $prism->get( $resource->{'uri'} )->{'content'} );
    
    foreach my $recall (  @{ $io->{'results'} }  )
    {
    
        print $prism->morph( $resource->{'source'}, $recall ), "\n";
    }
    
}

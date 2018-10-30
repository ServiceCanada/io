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
use XML::LibXML;
use XML::LibXML::XPathContext;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $dbh = DBI->connect(
    "dbi:SQLite:dbname=".$prism->parent('public')->sibling(  $prism->config->{'database'}->{'path'} )
    ,"","", { sqlite_unicode => 1 }
);


my $add = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'add'} );
my $update = $dbh->prepare( $prism->config->{'database'}->{'sql'}->{'update'} );

while ( my $resource = $prism->next() )
{
     my $io = $prism->download( $resource->{'uri'}, $resource->{'source'} );
     
     #next if ( $io == undef );
     
     my $xml = $io->slurp_utf8();
     
     $xml =~ s{xmlns="http://www.w3.org/2005/Atom"}{};
     
     my $dom = XML::LibXML->load_xml( string =>  $xml );
     
     foreach my $entry ( $dom->findnodes('//entry') ) {
         say 'Title:    ', $entry->findvalue('./title');
         say 'Id:    ', $entry->findvalue('./id');
     }
}


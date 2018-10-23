#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use YAML::Tiny;
use JSON;
use Prism;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

while( my $resource = $prism->next() )
{
   my $response = $prism->get( $resource->{'uri'} );
   
   if ( $response->{success} )
   {
        my $json = decode_json( $response->{content} );
        
        my $index = { data => [] };
        
        foreach my $event ( $json->{'data'} )
        {
            print encode_json $event;
            push @{ $index->{'data'} }, $prism->transform( $event, $resource );
        }
        
        use Data::Dumper;
        print Dumper( $index );
    }
  
}
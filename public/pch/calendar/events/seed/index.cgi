#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Path::Tiny qw/path/;
use YAML::Tiny;
use JSON::XS;
use Prism;


# =================
# = Globals =
# =================

my $datadir = path($0)->parent(2);

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'index.yml' );

my $coder = JSON::XS->new->utf8;

my $cind = 0;

while( my $resource = $prism->next() )
{
   my $response = $prism->get( $resource->{'uri'} );
   my $source =  $datadir->child( $resource->{'source'} )->touchpath;
   

   if ( $response->{success} )
   {
        my $json = $coder->decode( $response->{content});
        
        my $index = { created => time, data => [] };
        
        foreach my $event ( @{ $json->{'data'} } )
        {
            my $dataset = $prism->transform( $event, $resource );
            push @{ $index->{'data'} }, $dataset;
            
            #lets create this dataset
            $source->sibling( $dataset->{'id'}.'.json' )->spew_raw( $coder->encode( $dataset )  );
            
            $cind++;
        }
                   
        #lets create this dataset
        $source->spew_raw( $coder->encode( $index )  );
    }
  
}

$prism->message( data => { total => $cind/2 } );

#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Prism;
use JSON::MaybeXS;
use Path::Tiny qw/path/;
use Data::Dmp qw/dd/;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( 'index.yml' );



while ( my $resource = $prism->next() )
{
    my $file =  delete $resource->{'uri'};
    
    my $json = decode_json( path($0)->sibling( $file )->slurp );
    
    foreach my $record ( @{ $json } )
    {
        dd $prism->map( $record, $resource );
    }
 
}

# foreach my  ( @$json )
# {
#     my $uri = delete $record->{'uri'};
#
#     foreach ( )
#     dd $prism->map( $record );
# }
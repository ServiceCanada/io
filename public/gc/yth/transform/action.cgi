#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );
use v5.10;

use cPanelUserConfig;

use Prism;
use YAML::Tiny;
use Path::Tiny qw/path/;
use JSON::XS;
use Storable qw/dclone/;
#use Archive::Zip;

use Time::Piece;

# =================
# = PREPROCESSING =
# =================
my ( $partner, $api, $coder, $prism ) = (
    path($0)->parent(2)->child('csc'),
    path($0)->parent(2)->child('api'),
    JSON::XS->new->pretty->utf8,
    Prism->new( file => 'action.yml' )
    );

my $config = $prism->config;


while ( my $resource = $prism->next() )
{
    my $io = $prism->download( $resource->{'uri'}, $resource->{'source'}, 'uncompress' );
    
    unless ( $io  )
    {
        $io = path($0)->sibling( $resource->{'source'} );
    };
    
   foreach my $opp (@{ $coder->decode( $io->slurp_raw )->{'data'} })
   {
       
   }
}


$partner->child('index.json')->spew_raw( $coder->canonical->encode( $index ) );

$api->child('csc', 'en', 'index.json' )->touchpath->spew_raw( $coder->canonical->encode( normalize( $index, '_fr$', '_en$' ) ) );
$api->child('csc', 'fr', 'index.json' )->touchpath->spew_raw( $coder->canonical->encode( normalize( $index, '_en$', '_fr$' ) ) );

#my $zip = Archive::Zip->new();

#$zip->addTree( $api->absolute->realpath->stringify );
#$zip->overwriteAs({ filename => $api->sibling('all.zip')->absolute->realpath->stringify });



# ----------------------------------------------------------------------------------------------
# Functions
# ..............................................................................................

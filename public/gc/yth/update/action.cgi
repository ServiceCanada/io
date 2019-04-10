#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );
use v5.10;

use cPanelUserConfig;

use Prism;
use YAML::Tiny;
use Path::Tiny qw/path/;
use Archive::Zip;

use Time::Piece;

# =================
# = PREPROCESSING =
# =================
my $datadir = path($0)->parent(2)->child('api');
my $prism = Prism->new( file => 'action.yml' );
my $config = $prism->config;

my $now = localtime;

while ( my $resource = $prism->next() )
{
    my $io = $prism->download( $resource->{'uri'}, $resource->{'source'}, 'uncompress' );
    
    unless ( $io  )
    {
        say '   [skipping] '.$resource->{'uri'}.' not modified';
        next;
    };

    
}



    my $zip = Archive::Zip->new();

    $zip->addTree( $datadir->absolute->realpath->stringify );

    $zip->overwriteAs({ filename => $datadir->sibling('all.zip')->absolute->realpath->stringify });



# ----------------------------------------------------------------------------------------------
# Functions
# ..............................................................................................
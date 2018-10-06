#!/usr/bin/env perl
use common::sense;
use File::Spec;
use lib substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ) . '/cgi-lib' ;

use cPanelUserConfig;

use Furl;   
use Digest::SHA;
use Path::Tiny qw/path/;
use YAML::Tiny;
use Log::Tiny;

use JSON::MaybeXS;
use UUID::Tiny ':std';

use Encode::Encoder qw(encoder);
use MIME::Base64;
use POSIX;

use Mustache::Simple;
use Prism::Toolkit;

# =================
# = PREPROCESSING =
# =================
my ( $config, $http, $json, $base, $stache, $log, $from, $to ) = (
    YAML::Tiny->read( path($0)->sibling('index.yml')->stringify )->[0],
    Furl->new( timeout => 30, agent => 'Canada.ca Auditor v1.0' ),
    JSON::MaybeXS->new( utf8 => 1 ),
    path($0)->parent,
    Mustache::Simple->new,
    Log::Tiny->new( path($0)->parent(2)->child( 'metrics/pull.log') , '%t [seeder] %m%n' ),
    POSIX::strftime( '%Y-%m-%d', localtime( time() - (31*24*60*60) ) ),
    POSIX::strftime( '%Y-%m-%d', localtime( time() - (1*24*60*60)) )
);

my ( $username, $secret ) = ( $config->{'http'}->{'creds'}->{'username'},  $config->{'http'}->{'creds'}->{'secret'} );

my $prism = Prism::Toolkit->new( $config );

$log->INFO( "Analytics Data Pull started" );

foreach my $resource ( @{ $config->{'catalog'} } )
{
    my $properties = { %{ $config->{'http'}->{'common'} } , %{ $resource } };

    my $reportid = $http->post(
        $properties->{'prefetch'},
        [ 'X-WSSE' => generate( $username, $secret ) ],
        $stache->render( $base->child( $properties->{'content'} )->slurp_utf8, { to => $to, from => $from } )
    );

    my ( $wait ) = ( 1 );

    while( $wait )
    {
        my $report = $http->post(
            $properties->{'uri'},
            [ 'X-WSSE' => generate( $username, $secret ) ],
            $reportid->content
        );

        if ( $report->content =~ /"error":"report_not_ready"/ )
        {
            sleep $properties->{'sleep'};
            next;
        }

        $base->child( $properties->{'store'} )->absolute->spew_utf8( $report->content );
        $wait = 0;
    }
}

$log->INFO( "Analytics Data Pull completed" );

$prism->message( $config->{'mail'}->{'to'}, $config->{'mail'}->{'subject'}, $config->{'mail'}->{'message'} );


# ====================
# = HELPER FUNCTIONS =
# ====================

sub generate
{
    my( $username, $password ) = @_;
                
    my ( $nonce, $created ) = (
        uuid_to_string( create_uuid( UUID_V4 ) ),
        now_w3cdtf()
    );
    
    return join( ' ',
        'UsernameToken',
        'Username="'.$username.'",',
        'PasswordDigest="'.encode_base64( Digest::SHA::sha256( $nonce.$created.$password ) ).'",',
        'Nonce="'. encode_base64( $nonce ).'",',
        'Created="'.$created.'",',
        'Algorithm="SHA256"'
    );
}

sub now_w3cdtf {
    my ( $sec, $min, $hour, $mday, $mon, $year ) = gmtime();
    $mon++;
    $year += 1900;

    sprintf(
        '%04s-%02s-%02sT%02s:%02s:%02s.297Z',
        $year, $mon, $mday, $hour, $min, $sec,
    );
}
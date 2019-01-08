#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use IO::Uncompress::Gunzip qw(gunzip $GunzipError);
use Path::Tiny qw/path/;
use YAML::Tiny;
use JSON::XS;
use Prism;
use DateTime;
use Date::Format;
use Date::Language;
use Storable qw/dclone/;
	use Data::Dump;


# =================
# = Globals =
# =================

my $datadir = path($0)->parent(2);

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'action.yml' );

my $coder = JSON::XS->new->utf8;

my $cind = 0;

while( my $resource = $prism->next() ){

	my $response = $prism->get( $resource->{'uri'} );

	# lets skip if nothing is there
	next unless ( $response->{'success'} );

	path($0)->sibling( $resource->{'source'} )->touchpath->spew_raw( $response->{'content'});

	my $source = $datadir->child( $resource->{'source'} )->touchpath;

	my $rolodex = {};

	if ( $response->{success} ){

		$source->spew_raw( $response->{'content'} );

		my $json = $coder->decode( $response->{'content'} );

		foreach my $article (@{ $json->{'data'} } ) {
			# lets start the process
			# 1. location
			# 2. department
			# 3. type
			my ( $location, $dept, $type ) = ( 
				query($article, 'location'),
				query($article, 'dept'),
				query($article, 'type')
			);

			print dd( $location );

			# $rolodex = add( $rolodex, 'location', scrub( $_ ), $article ) for @{ $location };
			# $rolodex = add( $rolodex, 'department', scrub( $_ ), $article ) for @{ $dept };
			# $rolodex = add( $rolodex, 'type', scrub( $_ ), $article ) for @{ $type };
		}

	}

}

# $prism->message( data => { total => $cind/2 } );
###########################################################
# Helper functions
##########################################################
sub scrub 
{
	my ($text) = @_;
	$text =~ tr/[aAeEiIoOuU]//;
	return $text;
}

sub query
{
	my ( $source, $query, @entries) = @_;
	push @entries, $_->{'key'} for @{ $source->{$query} };
	return \@entries; 
}

sub add
{
	my ($catalog, $index, $key, $value ) = @_;

	if ( !exists $catalog->{$index}->{ $key } )
	{
		$catalog->{$index}->{ $key } = [];
	}

	push @{ $catalog->{$index}->{ $key } }, $value;

	return $catalog;

}
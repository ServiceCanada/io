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
use Storable qw/dclone/;


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

	my $response = $prism->get( $resource->{'uri'}, "isGZ" );

	# lets skip if nothing is there
	next unless ( $response->{'success'} );

	path($0)->sibling( $resource->{'source'} )->touchpath->spew_raw( $response->{'content'});

	my $source = $datadir->child( $resource->{'source'} )->touchpath;

	if ( $response->{success} ){

		my $json = $coder->decode( $response->{'content'} );

		my $index = { created => time, data => [], alerts => $json->{'alerts'} };

		my $locations = {};

		foreach my $event ( @{ $json->{'data'} } ){

			my $dataset = $prism->transform( $event, $resource );
			my $single =  dclone($dataset);

			$locations->{ $dataset->{'location'} }++ if ( $dataset->{'location'} ne '' );

			push @{ $index->{'data'} }, $dataset;

			$single->{'alerts'} = $json->{'alerts'};

			#lets create this dataset
			$source->sibling( $dataset->{'id'}.'.json' )->spew_raw( $coder->encode($single)  );

			$cind++;
		}

		# lets not forget the alerts
		$index->{'locations'} = [ map { name=> $_, nmb => $locations->{$_} + 1 }, sort { $locations->{$b} <=> $locations->{$a} } keys $locations ];

		#lets create this dataset
		$source->spew_raw( $coder->encode($index)  );
	}

}

# $prism->message( data => { total => $cind/2 } );

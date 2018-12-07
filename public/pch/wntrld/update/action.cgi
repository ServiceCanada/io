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

		my $index = { created => time, data => [], alerts => $json->{'alerts'}, dates => { earliest => DateTime->now(), latest => DateTime->now() } };

		my $locations = {};

		my $lang = formatdate( delete $resource->{'lang'} );

		foreach my $event ( @{ $json->{'data'} } ){

			my $dataset = $prism->transform( $event, $resource );

			my $single =  dclone($dataset);

			$locations->{ $dataset->{'location'} }++ if ( $dataset->{'location'} ne '' );

			push @{ $index->{'data'} }, $dataset;

			$single->{'alerts'} = $json->{'alerts'};

			# lets localize time
			$single->{'fdate'} = $lang->{'cx'}->time2str( $lang->{'format'}, int $single->{'start'} );

			#lets create this dataset
			$source->sibling( $dataset->{'id'}.'.json' )->spew_raw( $coder->encode($single)  );

			# datetime ranges
			my $day = getdatetime( $dataset->{'startdate'} );

			if ( DateTime->compare( $day, $index->{'dates'}->{'earliest'} ) < 0 ){
				$index->{'dates'}->{'earliest'} = $day;
			}

			if ( DateTime->compare( $day, $index->{'dates'}->{'latest'} ) > 0 ){
				$index->{'dates'}->{'latest'} = $day;
			}

			$cind++;
		}

		# lets set the range
		$index->{'dates'}->{'latest'} = $index->{'dates'}->{'latest'}->ymd;
		$index->{'dates'}->{'earliest'} = $index->{'dates'}->{'earliest'}->ymd;

		# lets not forget the alerts
		$index->{'locations'} = [ map { name=> $_, nmb => $locations->{$_} + 1 }, sort { $locations->{$b} <=> $locations->{$a} } keys $locations ];

		#lets create this dataset
		$source->spew_raw( $coder->encode($index)  );
	}

}

# $prism->message( data => { total => $cind/2 } );

sub formatdate{
	my ($lang) = @_;
	return {
		format => ( $lang eq 'en') ? '%A, %B %e, %Y' : 'Le %A %e %B %Y',
		cx => Date::Language->new( ( $lang eq 'en' ) ? 'English' : 'French' )
	};
}

sub getdatetime{
	my ($timestamp) = @_;
	my ( $year, $month, $day ) = split /-/, $timestamp;
	return DateTime->new(
		year => $year,
		month => $month,
		day => $day,
		time_zone  => 'America/Toronto'
	);
}

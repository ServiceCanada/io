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

use Mustache::Simple;
use Archive::Zip;


# =================
# = Globals =
# =================

my $datadir = path($0)->parent(2);
my $template = path($0)->sibling('.templates');
my $stache = Mustache::Simple->new();

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'action.yml' );

my $coder = JSON::XS->new->utf8;

my $cind = 0;

my $update = 0;

while( my $resource = $prism->next() ){

	my $io = $prism->download( $resource->{'uri'}, $resource->{'source'} , "decompress" );
    
    unless ( $io )
    {
        say "[winterlude] skipping resource not modified ".$resource->{'uri'};
        next;
    }
    
    my $tfile = $template->child( join('/', ( substr( $resource->{'source'}, 7, 2 ), 'data.tmpl') ) );
    
    $update = 1;
    
	my $source = $datadir->child( substr($resource->{'source'}, 6) )->touchpath;
    
	my $json = $coder->decode( $io->slurp_raw );

	my $index = { created => time, data => [], alerts => $json->{'alerts'}, dates => { earliest => DateTime->now(), latest => DateTime->now() } };

	my $destinations = {};

	my $lang = formatdate( delete $resource->{'lang'} );

	foreach my $event ( @{ $json->{'data'} } ){

		my $dataset = $prism->transform( $event, $resource );

		my $single =  dclone($dataset);

		$destinations->{ $dataset->{'destination'} }++ if ( $dataset->{'destination'} ne '' );

		push @{ $index->{'data'} }, $dataset;

		$single->{'alerts'} = $json->{'alerts'};

		# lets localize time
		$single->{'locale'}->{'date'} = $lang->{'cx'}->time2str( $lang->{'format'}, int $single->{'start'} );
        
		# lets localize time
		$single->{'locale'}->{'time'} = formattime( $lang->{'iso'}, $single->{'period'} );

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
	$index->{'destinations'} = [ map { name=> $_, nmb => $destinations->{$_} + 1 }, sort { $destinations->{$b} <=> $destinations->{$a} } keys $destinations ];

	#lets create this dataset
	$source->spew_raw( $coder->encode( $index ) );
    
    $index->{'data'} = $stache->render( $tfile->slurp_utf8 , $index );
    
    $index->{'data'} =~ s/[\n]+//sg;
    $index->{'data'} =~ s/[\s]+/ /g;
        
    $source->sibling( 'clndr.json' )->spew_raw( $coder->encode( $index ) );

}

if ( $update )
{

    my $zip = Archive::Zip->new();
    
    $zip->addTree( $datadir->child( $_ )->absolute->realpath->stringify, $_ ) for ('en', 'fr');
    
    $zip->overwriteAs({ filename => $datadir->child('all.zip')->absolute->realpath->stringify });
}

# $prism->message( data => { total => $cind/2 } );
###########################################################
# Helper functions
##########################################################
sub formattime
{
   my ( $lang,  @times ) = ( $_[0], split( /\s*-\s*/, $_[1] ) );
      
   my @formatted = ();
   
   foreach my $moment ( @times )
   {    
      my ($hour, $min, $daytime ) = split( /:/, $moment );
      
      if ( $lang ne 'en' )
      {
          push @formatted, ( int( $hour ).' h'.( ( $min ne '00' ) ? ' '.$min : '' ) );
          next;
      }
      
      $daytime = ( $hour > 11 ) ? 'pm' : 'am';
      
      $hour = ( $hour > 12 )  ? $hour - 12 : $hour;
     
      push @formatted, ( int( $hour ).':'.$min.' '.$daytime );
      
   }
  
   return ( $lang eq 'fr' ) ? join(  ' à ', @formatted ) : join( ' to ', @formatted ); 
}

sub formatdate
{
	my ($lang) = @_;
	return {
        iso => $lang,
		format => ( $lang eq 'en') ? '%A, %B %e, %Y' : 'Le %A %e %B %Y',
		cx => Date::Language->new( ( $lang eq 'en' ) ? 'English' : 'French' )
	};
}

sub getdatetime
{
	my ($timestamp) = @_;
	my ( $year, $month, $day ) = split /-/, $timestamp;
	return DateTime->new(
		year => $year,
		month => $month,
		day => $day,
		time_zone  => 'America/Toronto'
	);
}

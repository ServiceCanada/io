
#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;

use Path::Tiny qw/path/;
use YAML::Tiny;
use JSON::XS;
use Prism;
use Time::Piece;
use Time::Seconds;
use Mojo::URL;

use Mustache::Simple;
use Archive::Zip;
use Storable qw/dclone/;
use Data::Dmp;

# =================
# = Globals =
# =================

our $UPDATEZIP = 0;

my $api       = path($0)->parent(2)->child('api');
my $stache    = Mustache::Simple->new();
my $templates = path($0)->parent->child('.templates');


my $ziploc    = path($0)->parent(2)->child('feeds');

# =================
# = Time Pieces =
# =================
my $start = localtime;
my $floor = localtime->add_months( -3 );
my $ceil = localtime->add( ONE_WEEK );

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( file => 'action.yml' );

my @feeds = @{ $prism->config->{'feeds'} };

my $coder = JSON::XS->new->pretty->utf8;

my $cind = 0;

while ( my $resource = $prism->next() ) {
	
    my $response = $prism->get( $resource->{'uri'} .'?cb=' . $start->epoch );

    my $lang = $resource->{'lang'};

    next unless ( $response->{'success'} );

    my $store = $coder->decode( $response->{'content'} );
	
    for my $article ( @{ $store->{data} } ) {
        my $date = iso( $article->{'pubdate'} );
        my $dataset = {
            title    => trim( $article->{'title'} ),
			teaser   => trim( $article->{'teaser'} ),
			modifieddate => int( $article->{'modifieddate'} ),
            link     => $article->{'link'},
            publishedDate  => iso( $article->{'pubdate'} )
        };
			
        foreach my $fd (@feeds) {
            my ( $matches, @tags ) = ( 0, @{ $fd->{'tags'} } );

            for my $tag (@tags) {
                foreach my $aky ( @{ $article->{ $tag->{'category'} } } ) {
                    $matches++ if ( normalize( $aky->{'key'} ) eq $tag->{'key'} );
                }
            }

            if ( $matches >= scalar(@tags) ) {
                add( $dataset, $lang, dclone($fd) );
            }
        }

    }

}

if ( $UPDATEZIP > 0 )
{
    
    say " [altered] changed detected regenerating zip";
    
    my $zip = Archive::Zip->new();
    
    $zip->addTree( $api->child( $_ )->absolute->realpath->stringify, $_ ) for ('en', 'fr');
    
    $zip->overwriteAs({ filename => $ziploc->child('all.zip')->absolute->realpath->stringify });
}


###########################################################
# Helper functions
##########################################################
sub add {
    my ( $data, $lang, $feed ) = @_;
	
	my $date = epoch( $data->{'publishedDate'} );
	
	# lets not waste time on older or mistyped NR's	
	return if ( $ceil->epoch <= $date );
	
	my $now = localtime;
		
	if ( exists $feed->{'limit'} )
	{
	  $feed->{'ranged'} = (  $feed->{'limit'} =~ /\D/  ) ? shorten( $now, $feed->{'limit'}  ) : $feed->{'limit'} ;	
	}
	
	# lets only take what we need
	if ( $feed->{'ranged'} || $floor->epoch <= $date )
	{
		
		$feed->{ $_ } = $feed->{ $_ } // $prism->config->{'globals'}->{ $_ } for ('logo', 'limit');
		$feed->{ $_ } = $feed->{ $_ } // $prism->config->{'globals'}->{ $_ }->{ $lang } for ('id', 'subtitle');
	
	    json( $feed, $lang, $data );
	    #atom( $feed, $lang, $data );
	}
    
}

sub atom {
    my ( $feed, $lang, $data ) = @_;

    my $io = $api->child( $feed->{ $lang }->{'atom'} );

    my $src = ( $io->is_file ) ? $io->slurp_utf8 : $templates->child('atom/template.xml')->slurp_utf8;

    return if ( index( $src, $data->{'link'} ) != -1 );

    $io->touchpath->spew_utf8( $src . "\n" );

}

sub json {
    my ( $feed, $lang, $data ) = @_;
  
    my ( $io, $date ) = ( $api->child( $feed->{ $lang }->{'json'} ), epoch( $data->{'publishedDate'} ) );
	
    my $src = ( $io->is_file ) ? $io->slurp_raw : $templates->child('json/template.json')->slurp_raw;
    
     my $json = $coder->decode( $src );
     
     my ( $regen , @dataset ) = audit( $data, @{ $json->{'feed'}->{'entry'} } );
          
    return unless ( $regen ) ;
    	
	my @entries = sort { epoch( $b->{'publishedDate'} ) <=> epoch( $a->{'publishedDate'} )  } @dataset;
	
	if ( $feed->{'ranged'} )
	{
		if ( ref( $feed->{'ranged'} ) ne 'SCALAR' )
		{
			
			my @scoped = ();
			my $epoch = $feed->{'ranged'}->epoch;
			
			for my $item ( @entries )
			{
				push @scoped, $item if ( $epoch < epoch( $item->{'publishedDate'} ) );
			}
			
			$json->{'feed'}->{'entry'} = [ @scoped ];
			
			return update( $io, $coder->encode($json), $data->{'link'} );
		}
		
		$json->{'feed'}->{'entry'} = ( scalar(@entries) > $feed->{'ranged'} ) ?  [ @entries[0.. $feed->{'ranged'}-1 ] ]: [ @entries  ];
		
		return update( $io, $coder->encode($json), $data->{'link'} );
	}
	
	$json->{'feed'}->{'entry'} = ( scalar(@entries) > $feed->{'limit'} ) ? [ @entries[0.. $feed->{'limit'}-1 ] ] : [ @entries  ];
	
    return update( $io, $coder->encode($json), $data->{'link'} );
}

sub trim {
    my ($text) = @_;
    $text =~ s/^\s+|\s+$//g;
    return $text;
}

sub update
{
	my ( $fh, $data, $link ) = @_;
	
	if ( index( $data, '"'.$link.'"' ) != -1 )
	{
		$fh->touchpath->spew_raw( $data );
		$UPDATEZIP = 1;
	} 	
}

sub normalize
{
	my ( $text ) = @_;
	$text =~ s/[^a-zA-Z0-9]+//g;
	return lc($text);
}

sub shorten
{
	my ( $date, $time ) = @_;
	my @ins = split //, $time;
	my ( $tframe, $amount ) = ( pop(@ins), join('',@ins) );
	return ( $tframe eq 'm' ) ? $date->subtract( $amount * ONE_MONTH ) : $date->subtract( $amount * ONE_YEAR );
}

sub audit
{
    my ($data, @entries ) = @_;
    
    my ( $regen, $add ) = ( 0, 1 );
    
    for (my $idx = 0; $idx < scalar(@entries); $idx++) {
        
        if ( $data->{'link'} eq $entries[$idx]->{'link'} )
        {
            $add = 0;
            # lets see if we need to regenerate 
            if ( int( $data->{'modifieddate'} ) != int( $entries[$idx]->{'modifieddate'} ) )
            {
                $entries[$idx] = $data;
                $regen = 1;
            }
        }
    }
    
    # lets see if we need to add this to the entries
    if ( $add )
    {
        push @entries, $data;
        $regen = 1;
    }
        
   return ($regen, @entries );
}

sub iso
{
    my ( $timestamp ) = @_;
    return join( 'T', split( / /, $timestamp ) ).'-05:00';
}

sub epoch
{
    my ( $timestamp ) = @_;
    $timestamp =~ s/\-05\:00$/ \-0500/;
    return Time::Piece->strptime( $timestamp ,"%Y-%m-%dT%H:%M:%S %z")->epoch
}

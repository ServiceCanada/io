package Prism::HttpClient;
use common::sense;

use HTTP::Tiny;
use HTTP::CookieJar;
use IO::Uncompress::Gunzip qw(gunzip $GunzipError);
use Class::Tiny qw(http basedir);


sub BUILD{
	my ($self, $args) = @_;
    
    $self->basedir( $args->{'basedir'} );
    
    my $http = HTTP::Tiny->new();
    
    # lets set the agent
    $http->agent( ( $args->{'agent'} ) ? $args->{'agent'} : 'Prism v1.3rc' );
    
    # lets set the timeout
    $http->timeout( ( $args->{'timeout'} ) ? $args->{'timeout'} : 10 );
    
    # lets set the default headers
    my $defaults = { 'Accept-Encoding' => 'gzip' };
    
    if ( $args->{'default_headers'}  )
    {
        foreach my $key (keys %{ $args->{'default_headers'} } ) {
            $defaults->{$key} = $args->{'default_headers'}->{ $key };
        }
    }
    
    $http->default_headers( $defaults );
    
    # lets set the proxy if exists
    $http->proxy( $args->{'proxy'} ) if ( $args->{'proxy'} );
    
    # set default redirects
    $http->max_redirect( ( $args->{'max_redirect'} ) ? $args->{'max_redirect'} : 7 );
    
    # add a cookiejar
    # TODO: add functionality to load cookies via a path later
    $http->cookie_jar( HTTP::CookieJar->new );
	
	$self->http( $http );

	return $self;
}


sub get {
	my ( $self, $url, $forcedgz ) = @_;

	my $response = $self->http->get($url);
    
	return unless ( $response->{success} && length $response->{content} );

	if ( $response->{headers}{'content-encoding'} eq 'gzip' || $forcedgz ){
		my ( $content, $decompressed, $scalar, $GunzipError) = ( $response->{content} );

		gunzip \$content => \$decompressed,
		  or die "gunzip failed: $GunzipError\n";

		$response->{content} = $decompressed;
	}

	return $response;
}


sub post {
	return shift->http->post(@_);
}


sub head{
	return shift->http->head(@_);
}


sub download {

	my ($self, $url, $save, $gzipped ) = @_;

	$save = ( ref($save) eq 'Path::Tiny' ) ? $save : $self->basedir->child($save);

	$save->parent->mkpath() unless ( $save->parent->is_dir );

	my $res = $self->http->mirror( $url, $save->stringify );

	if ( $res->{status} == 304 ) {
		# print "$url has not been modified\n";
		return;
	}
    
    if ( $gzipped )
    {
        my ( $content, $decompressed, $scalar, $GunzipError) = ( $save->slurp_raw );
        
		gunzip \$content => \$decompressed,
		  or die "gunzip failed: $GunzipError\n";
         
          $save->spew_raw( $decompressed );
    }

	return $save;
}

1;

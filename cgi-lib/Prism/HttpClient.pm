package Prism::HttpClient;
use common::sense;

use HTTP::Tiny;
use IO::Uncompress::Gunzip qw(gunzip $GunzipError);
use Class::Tiny qw(http basedir);

sub BUILD
{
    my ($self, $args) = @_;
        
    my %props  = (
        timeout => ( $args->{'timeout'} ) ? delete $args->{'timeout'} : 10,
        agent => ( $args->{'agent'} ) ? delete $args->{'agent'} : 'Prism crawler v1.0rc',
        default_headers => { qw'Accept-Encoding gzip' }
    );
    
    if ( $args->{'default_headers'}  )
    {
        $props{'default_headers'} = {
            %{ $props{'default_headers'} },
            %{ delete $args->{'default_headers'} }
        };
    }
       
    $self->basedir( $args->{'basedir'} );
    
    $self->http( HTTP::Tiny->new( %props ) );
        
    return $self;
}


sub get 
{
    my ( $self, $url ) = @_;
    
    sleep(1);
    
    my $response = $self->http->get( $url );
      
    return unless ( $response->{success} && length $response->{content} );
    
    if ( $response->{headers}{'content-encoding'} eq 'gzip' )
    {
        my ( $content, $decompressed, $scalar, $GunzipError) = ( $response->{ content } );

        gunzip \$content => \$decompressed,
            or die "gunzip failed: $GunzipError\n"; 

        $response->{ content } = $decompressed;
    }
        
    return $response;
}

sub post 
{
    return shift->http->post( @_ );
}

sub head
{
    return shift->http->head( @_ );
}

sub download 
{
    
    my ($self, $url, $save ) = @_;
    
    $save = ( ref($save) eq 'Path::Tiny' ) ? $save : $self->basedir->child( $save ) ;
    
    $save->parent->mkpath() unless ( $save->parent->is_dir );
    
    my $res = $self->http->mirror( $url , $save->stringify );
    
    if ( $res->{status} == 304 ) {
        print "$url has not been modified\n";
        return;
    }
    
    return $save;
}

1;

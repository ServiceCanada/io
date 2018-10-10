package Prism::HttpClient;
use common::sense;
use HTTP::Tiny;
use Class::Tiny qw(http basedir);

sub BUILD
{
    my ($self, $args) = @_;
        
    my %props  = (
        timeout => ( $args->{'timeout'} ) ? delete $args->{'timeout'} : 10,
        agent => ( $args->{'agent'} ) ? delete $args->{'agent'} : 'Prism crawler v1.0rc'
    );
    
    $self->basedir( $args->{'basedir'} );
    
    $self->http( HTTP::Tiny->new( %props ) );
    
    return $self;
}


sub get 
{
    return shift->http->get( @_ );
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
        
    my $res = $self->http->mirror( $url , $save->stringify );

    if ( $res->{status} == 304 ) {
        print "$url has not been modified\n";
        return;
    }
    
    return $save;
}

1;

package Prism::Mapper;
use common::sense;

use Mustache::Simple;
use Digest::SHA qw/sha256_hex/;
use HTML::Strip;
use Date::Manip::Date;

use Data::Dmp;

use Class::Tiny qw(basedir map),{
    stache => Mustache::Simple->new()
};

sub BUILD
{
    my ($self, $args) = @_;

    $self->basedir( delete $args->{'basedir'} );
    
    $self->map( $args );
    
    return $self;
}


sub transform 
{
    my ( $self, $data, $overrides ) = @_;
    
    # lets get rid of some other keys local file io keys
    delete $overrides->{ $_ } for ( 'source', 'uri' );
    
    my $map = { %{ $self->map() }, %{ $overrides } };
    
    my $dataset = { $self->_pluck(), %{ $data } };
        
    my $transform = {};
    
    foreach my $idx (keys %{ $map } )
    {
        $transform->{$idx} = $self->stache->render( $map->{$idx}, $dataset );
    } 
    
   return $transform;
}


sub _pluck
{
    my ( $self ) = shift ;
    
    return (
        '-sha256' => sub { return sha256_hex( $self->stache->render( shift ) ) },
        '-epoch' => sub { my $dt = Date::Manip::Date->new; $dt->parse( $self->stache->render( shift ) ); return $dt->secs_since_1970_GMT() },
        '-striptags' => sub { return HTML::Strip->new->parse( $self->stache->render( shift ) ) },
        '-getlink' => sub { my ( $text, $url ) = ( $self->stache->render( shift ), '') ; while ( $text =~ m{(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))}go ) { $url = $1 }; return $url }
        );
 
}


1;

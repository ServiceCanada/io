package GC::News::Feeds::JSON;

use Class::Tiny qw/dom/;
use DateTime;
use DateTime::Format::ISO8601::Format;
use JSON::XS;

sub BUILD
{
    my ($self, $args) = @_;
    
    $self->dom( $args );
}

sub add
{    
    my ( $self, $article ) = @_;
      
    # We may want to filter here
    return push( @{ $self->dom->{feed}->{entry} }, {
          link => $article->{link},
          teaser => $article->{teaser},
          publishedDate => $self->_date( $article->{published} ),
          title => $article->{title}
      });
}

sub render
{
    my ( $self, $args ) = @_;
    return JSON::XS->new->utf8->encode( $self->dom );
}

sub _date
{
   my ( $self, $epoch ) = @_;
   
   my ( $datetime, $format) = (
       DateTime->from_epoch( epoch => $epoch ),
       DateTime::Format::ISO8601::Format->new( time_zone => 'America/Toronto')
    );
   
   return $format->format_datetime( $datetime );
}


1;
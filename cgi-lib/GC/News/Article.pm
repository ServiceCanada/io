package GC::News::Article;

use Class::Tiny qw/title abstract url published modified language tags type dept/;

use DateTime;
use feature ':5.10';


=item BUILD()

We are leveraging Class::Tiny overload property to ensure that we can create a custom GC::News::Article class with the appropiate details

=cut

sub BUILD
{
     my ($self, $args) = @_;
     
     $self->published( $self->_date( delete $args->{ pubdate } ) );
     
     $self->modified( int( delete $args->{ modifieddate } ) );
     
     $self->title( delete $args->{ title } );
     
     $self->abstract( delete $args->{ teaser } );
     
     $self->url( delete $args->{ link } );
     
     $self->language( delete $args->{ lang } );
     
     $self->type( $args->{'type'}->[0]->{'text'} );
     
     $self->dept( $args->{'dept'}->[0]->{'text'} );
     
     $self->tags( $args );
     
     # last minute tweaks
     
     $self->modified( int( $self->modified / 1000 ) );
     
};

=item export()

This function exports the article object in a wat that is Mojo::SQLite Insert friendly

=cut

sub export
{
    my ( $self, $deptid ) = @_;
    return { link => $self->url, title => $self->title, teaser => $self->abstract, modified => $self->modified, published => $self->published, lang => $self->language, author => $self->dept, type => $self->type  }
}

sub _date
{
    my ($self, $datetime) = @_;
    my ( $date, $time) = split /\s+/, $datetime;
    # date
    
    my %args;
    
    @args{'year','month','day'} = split /-/, $date;
    @args{'hour','minute','second'} = split /:/, $time;
    
    my $dt = DateTime->new(%args, time_zone  => 'America/Toronto');
    
    return $dt->epoch;
}


1;
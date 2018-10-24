package Prism::Mail;

use common::sense;
use Class::Tiny qw(mail basedir stache);
use Mail::Sendmail;
use Mustache::Simple;
use Data::Dmp;

sub BUILD
{
    my ($self, $args) = @_;
    
    $self->basedir( delete $args->{'basedir'} );
        
    $self->mail( $args );
    
    $self->stache( Mustache::Simple->new() );
    
    return $self;
}

sub message
{
    
    my ( $self, $args ) = ( shift, { @_ } );
    
    my $data = ( $args->{'data'} ) ? $args->{'data'} : { time => time };
    
    my ( $to, $from, $subject, $body ) = (
      ( $args->{'to'} ) ? $args->{'to'} : $self->mail->{'to'},
      ( $args->{'from'} ) ? $args->{'from'} : $self->mail->{'from'},
      ( $args->{'subject'} )
          ? $self->stache->render( $args->{'subject'}, $data )
          : $self->stache->render( $self->mail->{'subject'}, $data ),
      ( $args->{'body'} )
          ? $self->stache->render( $args->{'body'}, $data )
          : $self->stache->render( $self->mail->{'body'}, $data )
    );
    
    if ( $self->mail->{'host'} ne 'debug' )
    {
            
        return Mail::Sendmail::sendmail(
             To   => $to,
             From => $from,
             Subject => $subject,
             Message => $body
        
        ) or die $Mail::Sendmail::error;
        
    }
    
    say " [Debug mode] activated since not on server";
    say " [Email Message] .. send";
    say " To: $to";
    say " From: ".$from;
    say " Subject: $subject";
    say "\n";
    say "$body";
    
    return -1;
}

1;

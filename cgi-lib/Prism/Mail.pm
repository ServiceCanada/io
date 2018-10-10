package Prism::Mail;

use common::sense;
use Class::Tiny qw(mail basedir);
use Mail::Sendmail;
use Data::Dmp;

sub BUILD
{
    my ($self, $args) = @_;
    
    $self->basedir( delete $args->{'basedir'} );
        
    $self->mail( $args );
    
    return $self;
}

sub message
{
    
    my ( $self, $to, $subject, $body ) = @_;
    
    if ( $self->mail->{'host'} ne 'local' )
    {
            
        return Mail::Sendmail::sendmail(
             To   => $to,
             From => $self->mail->{'from'},
             Subject => $subject,
             Message => $body
        
        ) or die $Mail::Sendmail::error;
        
    }
    
    say " [Debug mode] activated since not on server";
    say " [Email Message] .. send";
    say " To: $to";
    say " From: ".$self->mail->{'from'};
    say " Subject: $subject";
    say "\n";
    say "$body";
    
    return -1;
}

1;

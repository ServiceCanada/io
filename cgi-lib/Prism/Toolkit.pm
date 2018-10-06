package Prism::Toolkit;

use v5.16;

sub new
{
    my ( $class, $args ) = @_;
    
    return bless $args, $class;
}

sub mail { $_[0]->{'mail'}->{ $_[1] } };

sub message
{
    my ( $self, $to, $subject, $body ) = @_;
    
    if ( ! exists $self->{'mail'}->{'host'} or  $self->{'mail'}->{'host'} eq 'localhost' )
    {
        
        require Mail::Sendmail;
    
        return Mail::Sendmail::sendmail(
             To   => $to,
             From => $self->mail( 'from' ),
             Subject => $subject,
             Message => $body
        
        ) or die $Mail::Sendmail::error;
        
    }
    
    say " [Debug mode] activated since not on server";
    say " [Email Message] .. send";
    say " To: $to";
    say " From: ".$self->mail( 'from' );
    say " Subject: $subject";
    say "\n";
    say "$body";
    
    return;

}



1;

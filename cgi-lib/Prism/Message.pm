package Prism::Message;

use Mail::Sendmail;
use constant EOL => "\n";

=head1 NAME

Prism::Message - A plugin to Prism that allowes prism to send mail

=head1 VERSION

Version 1.0

=cut

$VERSION = '1.0';
$errstr  = '';

=head1 SYNOPSIS

This module aims is an plugin for Prism and shoud not be interface directly.

=head1 FUNCTIONS

=head2 new

Create a new Prism::Message object, with the existing C< Prism > mail
properties.

=cut

sub new {
    my ( $class, $args ) = @_;
    return bless $args, $class;
}

=head2 message

Sends a message using either C< Mail::Sendmail > or *STDOUT, with the existing C< Prism > mail
properties.

=cut

sub message {
    my ( $self, $to, $subject, $body ) = @_;

    if ( ( !exists $self->{'host'} or $self->{'host'} ne 'debug' )
        and $self->{'from'} )
    {

        require Mail::Sendmail;

        return Mail::Sendmail::sendmail(
            To      => $to,
            From    => $self->{'from'},
            Subject => $subject,
            Message => $body

        ) or die $Mail::Sendmail::error;

    }

    return _debug(@_);

}

sub _debug {
    my ( $self, $to, $subject, $body ) = @_;

    return join(
        ' [Prism] - Debug - ',
        ' [Prism] - Message - send',
        ' To: $to',
        ' From: ' . $self->{'from'},
        ' Subject: ' . $subject,
        EOL, $body
    );

}

1;

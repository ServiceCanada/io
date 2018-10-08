package Prism::Mapper;

use Mustache::Simple;
use Time::Piece;
use Digest::SHA qw/sha256_hex/;
use Data::Dmp;

use constant {
    EOL => "\n",
    STACHE => 0,
    MAP => 1
};

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
    
    return bless [
        Mustache::Simple->new(),
        $args
    ], $class;
}

=head2 transform

Sends a message using either C< Mail::Sendmail > or *STDOUT, with the existing C< Prism > mail
properties.

=cut

sub transform {
    my ( $self, $context ) = @_;
    
    $context = { $self->_pluck(), %$context };
    
    my $map = $self->[MAP];
    
    foreach $idx (keys %{ $map } )
    {
        $map->{$idx} = $self->[STACHE]->render( $map->{$idx}, $context );
    
    } 
    
   return $map;
    
}

sub _pluck
{
    my $self = shift;
    
    return (
        '-sha256' => sub { return sha256_hex( $self->[STACHE]->render( shift ) ) },
        '-epoch' => sub { return Time::Piece->strptime( $self->[STACHE]->render( shift ), '%Y%m%d' )->epoch },
        '-array' => sub { 
            my $reference = shift;
            dd  $self->[STACHE]->render( $_[0] );
            if (ref $_[0] ne 'ARRAY' or ref $_[0] ne 'HASH' ) { return [ $self->[STACHE]->render( $_[0] ) ] };
            if (ref $_[0] eq 'HASH' ) { return shift }
        }
    );
}



1;

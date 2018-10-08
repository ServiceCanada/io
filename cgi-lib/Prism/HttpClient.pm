package Prism::HttpClient;

use HTTP::Tiny;
use v5.16;
use File::Basename;
use Path::Tiny qw/path/;
use Data::Dmp;

sub new {
    my ( $class, $args ) = ( shift, { @_} );
    my  $http = HTTP::Tiny->new( @_ );
    return bless [ $http, $args ], $class;
}

sub get
{
    say "   [fetch] GET $_[1]";
    return shift->[0]->get(@_);
}

sub post
{
    say "   [fetch] POST $_[1]";
    return shift->[0]->post(@_);
}

sub head
{
    say "   [fetch] HEAD $_[1]";
    return shift->[0]->head(@_);
}

sub download
{
    my ($self, $url, $saveas ) = @_;
    my $file = path( $0 )->sibling( $saveas ) ;
    my $res = $self->[0]->mirror( $url , $file->stringify );
    if ( $res->{success} ) {
        print "$url is up to date\n";
    }
    
    return $file;
}

sub profile
{
    return  dmp shift->[1];
}

1;

package Prism::HttpClient;

use HTTP::Tiny;
use constant HTTP => 0;
use v5.16;
use File::Basename;
use Path::Tiny qw/path/;
use Data::Dmp;

sub new {
    my ( $class, $args ) = ( shift, { @_} );
    my  $http = HTTP::Tiny->new( @_ );
    return bless [ $http ], $class;
}

sub get
{
    say "   [fetch] GET $_[1]";
    return shift->[HTTP]->get(@_);
}

sub post
{
    say "   [fetch] POST $_[1]";
    return shift->[HTTP]->post(@_);
}

sub head
{
    say "   [fetch] HEAD $_[1]";
    return shift->[HTTP]->head(@_);
}

sub download
{
    my ($self, $url, $saveas ) = @_;
    my $file = path( $0 )->sibling( $saveas ) ;
    my $res = $self->[HTTP]->mirror( $url , $file->stringify );
    if ( $res->{success} ) {
        print "$url is up to date\n";
    }
    
    return $file;
}

1;

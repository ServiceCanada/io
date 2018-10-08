package Prism;

use YAML::Tiny;
use Path::Tiny qw/path/;
use Log::Tiny;
use File::Spec;
use Prism::HttpClient;

use Carp;

use constant EOL => "\n";

=head1 NAME

Prism - A YAML driven console based data worker

=head1 VERSION

Version 1.0

=cut

$VERSION = '1.0';
$errstr  = '';

$iterator = 0;
$catalog = 0;
$basedir = path($0)->parent->absolute;
$httpclient = undef;


=head1 SYNOPSIS

This module aims to be a flexiable YAML driven web worker 
to help consume and deliver API based services for static or incompatible datasets.

Its use is very straight forward:

    use Prism;

    my $prism = Prism->new( 'config.yml' ) or 
      die 'Could not load! (' . Prism->errstr . ')';
    
    # lets run a diagnostic (if we want to);
    say $prism->diagnostic();

    $prism->email( 'example@example.org', 'this is a test email', 'this the body of the email' );

=head1 FUNCTIONS

=head2 new

Create a new Prism object.  You must define pass path to the 
config file.

=cut

sub new {
    my ( $class, $filename ) = @_;

    return _error('No valid configfile provided')
      if ( !$class->base( $filename )->exists );

    my $props =
      YAML::Tiny->read( $class->base($filename, 1) )->[0];
    
    if ( exists $props->{'catalog'} )
    {
       $catalog = scalar( @{ $props->{'catalog'} } ); 
    }
      
    return bless $props, $class;
}

=head2 errstr

Called as a class method, C< Prism->errstr > reveals the 
error that Prism encountered in creation or invocation.

=cut

sub errstr { $errstr; }
sub _error { $errstr = shift; undef; }

=head2 diagnostic

This method outputs a small self-check from Prism to ensure
you have everything its needs

=cut

sub diagnostic {
    my $self = shift;

    return join( EOL,
        "Basedir: " . $self->base(),
        "Mail: " . ( $self->{'mail'} ) ? $self->_inspect('mail') : " n/a ",
        "Catalog: " . ( $self->{'catalog'} )
            ? scalar @{ $self->{'catalog'} } . " items available"
            : " 0 items ",
        "HttpClient: " . ( $self->{'http'} ) ? $self->_inspect('http')
            : " n/a "
    );
}


sub _inspect {
    my ( $self, $section ) = (@_);

    my $output = $section . " // ";

    $output .= " $_ -> " . $self->{$section}->{$_} .','
      for keys %{ $self->{$section} };

    return $output;
}

=head2 pluck

This get internal config structure for a passed value * only one level

=cut

sub pluck { shift->{shift} }

=head2 get

This is a getter to return the value in a config. **Dot Notation Friendly**


    my $dbpath = $prism->get('database.path'); # 'database/path'
    
    my $dsn = $prism->get('database.path', 'dbi:SQLite:dbname='); # '   database/path'
    

=cut

sub get {
    
    require Mustache::Simple;
    
    my ($self, $notation, $prefix ) = @_;
    
    my $value = Mustache::Simple->new->render( '{{ '.$notation.' }}', $self );
    
    return  ($prefix) ? $prefix.$value : $value;
}

=head2 closest

This is a helper function to return the closest named directory from the basedir.


=cut

sub closest {
        
        my ( $self, $needle, $default ) = @_;
    
        return $basedir unless ( $needle ); # just return self if no search if performed
    
        my $path = $basedir;

        while ( ! $path->is_rootdir ) {
        
            return $path if ( $path->basename eq $needle  );
        
            $path = $path->parent;
        }
    
        return ( $default ) ? Path::Tiny::path( $default )->absolute : undef;

}

=head2 base

This returns the absolute path from the base of a string.


=cut

sub base {
    
    my ($self, $path, $stringify ) = @_;
    
    if ( not defined $path )
    {
        return $basedir->stringify;
    }
    
    $path = $basedir->child( $path )->absolute;
    
    return  ( $stringify ) ? $path->stringify : $path;
}


=head2 email

This sends a email message using sendmail. If a hostname is set it will default to
a console.log output message

=cut

sub email {

    require Prism::Message;

    return Prism::Message->new( shift->{'mail'} )->message(@_);
}

=head2 map

This transforms an object with set mapping in the YAML file.

=cut

sub map
{
    my ( $self, $context, $overrides ) = @_;
    
    require Prism::Mapper;
    
    my $props = $self->{'http'}->{'map'};
    
    if ( $overrides )
    {
        $props = { %{ $self->{'http'}->{'map'} }, %{ $overrides } };
    }
    
    return  Prism::Mapper->new(  $props  )->transform( $context );
}

=head2 next

A small iterator for the catalog

=cut

sub next
{
    my ( $self ) = @_;
    
    my $idx = $iterator++;
    
    if ( $idx < $catalog )
    {
        return $self->{'catalog'}->[ $idx ]; 
    }
    
    $iterator = 0;    
}

=head2 next

A small iterator for the catalog

=cut

sub fetch
{
    my ( $self, $url, @args ) = @_;
    
    if ( ! defined $httpclient )
    {
        $httpclient = Prism::HttpClient->new( @args );
    }
    
   return $httpclient->get( $url );
       
}

sub download
{
    my ( $self, $url, $saveas, @args ) = @_;
    
    if ( ! defined $httpclient )
    {
        $httpclient = Prism::HttpClient->new( @args );
    }
    
   return $httpclient->download( $url, $saveas );
       
}

1;

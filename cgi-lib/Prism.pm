package Prism;

use YAML::Tiny;
use Path::Tiny qw/path/;
use Log::Tiny;
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

    my $base = path($0)->parent;

    return _error('No valid configfile provided')
      if ( !$base->child($filename)->exists );

    my $props =
      YAML::Tiny->read( $base->child($filename)->absolute->stringify )->[0];
    
    if ( exists $props->{'catalog'} )
    {
       $catalog = scalar( @{ $props->{'catalog'} } ); 
    }
      
    return bless { %$props, _basedir => $base }, $class;
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
        "Basedir: " . $self->{'_basedir'}->absolute->stringify,
        "Mail: " . ( $self->{'mail'} ) ? $self->_inspect('mail') : " n/a ",
        "Catalog: " . ( $self->{'catalog'} )
            ? scalar @{ $self->{'catalog'} } . " items available"
            : " 0 items ",
        "HttpClient: " . ( $self->{'http'} ) ? $self->_inspect('http')
            : " n/a "
    );
}
sub _get { shift->{shift} }

sub _inspect {
    my ( $self, $section ) = (@_);

    my $output = $section . " // ";

    $output .= " $_ -> " . $self->{$section}->{$_} .','
      for keys %{ $self->{$section} };

    return $output;
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

1;

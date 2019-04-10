package GC::News::Feeds::ATOM;

use Class::Tiny qw/dom/;
use DateTime;
use DateTime::Format::ISO8601::Format;
use XML::LibXML;

sub BUILD
{
    my ($self, $args) = @_;
    
    $self->dom( XML::LibXML::Document->new('1.0', 'UTF-8') );
    
    my $root = $self->dom->createElement('feed');
    $root->setAttribute('xmlns', 'http://www.w3.org/2005/Atom' );
    
    # ----------------------------------
    # ATOM Properties
    # ----------------------------------
    my $atom = delete $args->{'atom'};
    
    $args = { %$args, %$atom } ;
    
    
    foreach my $elm ('title', 'id', 'logo', 'subtitle' ) {
                   
        my $node = $self->dom->createElement( $elm );
        
        my $text = ( exists $args->{$elm}->{'en'} )
                        ? $args->{ $elm }->{ $args->{'lang'} }
                        : $args->{$elm} ;
        
        $node->appendText( $text );
        $root->appendChild( $node );
    }
    
    # updated
    
    my $updated = $self->dom->createElement('updated');
    $updated->appendText( $self->_date( DateTime->now->epoch ) );
    $root->appendChild( $updated );

    # ----------------------------------
    # ROOT Element
    # ----------------------------------
    $self->dom->setDocumentElement($root);
 
}

sub add
{    
    my ( $self, $article ) = @_;
        
    my ( $root, $node, $subnode ) = ( 
        $self->dom->createElement('entry'),
        $self->dom->createElement('title'),
        $self->dom->createElement('name')
    );
    
    # title;
    $node->appendText( $article->{'title'} );
    $root->appendChild( $node );
    
    # id
    $node = $self->dom->createElement('id');
    $node->appendText( $article->{'link'} );
    $root->appendChild( $node );
    
    # summary
    $node = $self->dom->createElement('summary');
    $node->setAttribute('type','html');
    $node->appendText( $article->{'teaser'} );
    $root->appendChild( $node );
    
    # author
    $node = $self->dom->createElement('author');
    # author / name
    $subnode = $self->dom->createElement('name');
    $subnode->appendText( $article->{'author'} );
    $node->appendChild( $subnode );
    $root->appendChild( $node );
	
	# type
    $node = $self->dom->createElement('category');
    $node->setAttribute('term', $article->{'type'} );
    #$node->appendText( $article->{'type'} );
    $root->appendChild( $node );
    
    # updated
    $node = $self->dom->createElement('updated');
    $node->appendText( $self->_date(  $article->{'published'} ) );
    $root->appendChild( $node );
    
    # link
    $node = $self->dom->createElement('link');
    $node->setAttribute('href', $article->{'link'} );
    $root->appendChild( $node );

    $self->dom->documentElement->appendChild( $root );

}

sub render
{
    my ( $self, $args ) = @_;
    return $self->dom->toString;
}

sub _date
{
   my ( $self, $epoch ) = @_;
   
   my ( $datetime, $format) = (
       DateTime->from_epoch( epoch => $epoch ) ,
       DateTime::Format::ISO8601::Format->new( time_zone => 'America/Toronto')
       );
   
   return $format->format_datetime( $datetime );
}



1;
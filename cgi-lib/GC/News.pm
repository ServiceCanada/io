package GC::News;

use Class::Tiny qw/source path database json sql/;


use Path::Tiny qw/path/;
use JSON::XS;

use GC::News::Article;
use GC::News::Database;
use GC::News::SQL;

use Carp;
use Time::Piece;


sub BUILD
{
    my ($self, $args) = @_;
    
    for my $req ( qw/path/ )
    {
        croak "$req attribute required" unless defined $args->{$req};
    }
    
    $self->json( JSON::XS->new->utf8 );
    
    $self->database( GC::News::Database->new( file => $args->{'path'} ) );
    
    $self->sql( GC::News::SQL->new() );
    
}


=item articles( type, lang, floor(optional), [tags] )

This function queries for articles in the database

@returns: {Mojo::Collection}

=cut

sub articles
{
    my ( $self, $lang, $floor, @tags ) = @_;
    
    return $self->query( $self->sql->articles( $lang, $floor ) ) unless ( scalar(@tags) );
    
    return $self->query( $self->sql->articles( $lang, $floor, @tags) ) if ( ref $tags[0] eq 'HASH' );

    my ( $seen, @collection ) = ();

    foreach my $xors (@tags) {

        my $results = $self->query( $self->sql->articles( $lang, $floor ,@{$xors} ) );

        if ( $results->size() ) {
            $results->each(
                sub {
                    my ($art) = @_;

                    return if ( $seen->{ $art->{link} }++ );

                    push( @collection, $art );
                }
            );
        }

    }

    return Mojo::Collection->new(@collection)
      ->sort( sub { $b->{published} <=> $a->{published} } );
}

sub clear
{
     return shift->database->clear();
}

sub parse
{
    my ($self, $lang, @articles) = @_;
    
    my $NEEDUPDATE = 0;
    
    foreach my $article ( @articles )
    {
        
        $article = GC::News::Article->new( { %$article, lang => $lang } );
        # Preprocess to look for change
        if ( $self->database->exists( 'articles', { link => $article->url } ) )
        {
            
            next if ( $self->database->exists( 'articles', { link => $article->url,  modified => $article->modified } ) );
            
            print "   [deleting] [modified] ". $article->url. "\n";
             
            $self->database->delete( 'articles', { link => $article->url  } );
        }
        
        $NEEDUPDATE = 1;
            
        my $id =  $self->database->insert('articles', $article->export() );
    
        foreach my $group (keys $article->tags )
        {
            my @tags = @{ $article->tags->{ $group } };
        
            next unless ( scalar( @tags ) );
        
            foreach my $tag ( @tags )
            {
                
                next unless (keys $tag);
                
                my $tid = $self->database->firstOrCreate('tags', { id => join( '-', $group , $tag->{'key'} ) }, { $lang => $tag->{'text'} } );
            
                $self->database->insert('article_tag', { article_id => $id, tag_id => $tid } );
            }
        }
           
    }
    
    return $NEEDUPDATE;
}


sub query
{
    my ($self, $sql ) = @_;
    
   return $self->database->query( $sql )->hashes;
}

1;
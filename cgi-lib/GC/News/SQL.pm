package GC::News::SQL;

use Class::Tiny;

use Time::Piece;
use Time::Seconds;

=item articles( $lang, $floor, @tags )

This function query the database for a specific set of tags

@returns: Mojo::Collection of Hashes

=cut

sub articles
{
    my( $self, $lang, $floor, @tags ) = @_;
        
    $floor = $self->timebox( $floor );
    
    if ( @tags )
    {
        return $self->_filtered( $lang, $floor , @tags );
    }
    
    return $self->_all( $lang, $floor );
}

=item _filtered( $lang, $floor, @tags )

This returns the SQL for a filtered article list

@returns: {String} SQLStatement

=cut
sub _filtered
{
    my( $self, $lang, $floor, @tags ) = @_;
    
    @tags = map { join('-', $_->{category}, $_->{key} )  } @tags ;
    
    my $sql = join(' ', 
        'SELECT articles.rowid AS rowid, articles.link AS link, articles.title AS title, articles.teaser AS teaser, articles.published AS published, articles.author AS author, articles.type AS type',
        'FROM articles',
        'JOIN article_tag ON articles.rowid = article_tag.article_id',
        'JOIN tags ON article_tag.tag_id = tags.rowid',
        'WHERE tags.id IN ('. join( ',', map { "'$_'" } @tags ).') AND articles.lang=\''.$lang.'\' AND articles.published >='.$floor,
        'GROUP BY articles.rowid',
        'HAVING COUNT(DISTINCT tags.id)='.scalar(@tags),
        'ORDER BY articles.published DESC',
        'LIMIT 100'
    );
    
    #print "-"x45,"\n",$sql,"-"x45,"\n";
    #exit;
  
    return $sql;
}

=item _all( $lang, $floor, @tags )

This returns the SQL for a all list

@returns: {String} SQLStatement

=cut
sub _all
{
    my( $self, $lang, $floor ) = @_;

   my $sql = join(' ', 
        'SELECT articles.rowid AS rowid, articles.link AS link, articles.title AS title, articles.teaser AS teaser, articles.published AS published, articles.author AS author, articles.type AS type',
        'FROM articles',
        'WHERE articles.modified >='.$floor.' AND articles.lang=\''.$lang.'\'',
        'ORDER BY articles.published DESC',
        'LIMIT 100'
    );
    
    return $sql;
}

=item timebox( $self, $timebox )

This function takes a human readable value (i.e. 1y or 3m ) and returns the epoch seconds from that time.

@returns: {int} epoch seconds

=cut
sub timebox
{
    my $now = localtime;
    
	unless ( $_[1] )
    {
        return $now->subtract( 3 * ONE_MONTH )->epoch;
    }
    my ( $self, $timebox ) = @_;
    
	my @ins = split //, $timebox;
    
	my ( $tframe, $amount ) = ( pop(@ins), join('',@ins) );
	
    return ( $tframe eq 'm' ) 
        ? $now->subtract( $amount * ONE_MONTH )->epoch
        : $now->subtract( $amount * ONE_YEAR )->epoch;
}

1;
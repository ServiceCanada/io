package GC::News::Database;

use Class::Tiny qw/dbh/;

use Mojo::SQLite;
use Mojo::Collection;

use Time::Piece;
use Time::Seconds;

sub BUILD {
    my ( $self, $args ) = @_;

    my $sql = Mojo::SQLite->new->from_filename( $args->{'file'},
        { RaiseError => 0, PrintError => 0 } );

    $self->dbh($sql);

}

=item clear( $migration-path )

This function resets the database to empty. **CAUTION** this clears all the contents in the database and rebuilds its tables.

@returns: void

=cut

sub clear {
    return $_[0]->dbh->migrations->from_data( $_[1] )->migrate(0)->migrate;
}

=item firstOrCreate( $table, $properties )

This function will query the datable table looking to see if the record already exists. If not it will create and return its set record_id

@returns: (int) record_id

=cut

sub firstOrCreate {
    my ( $self, $table, $props, $update ) = @_;
    
    my $rcd = $self->dbh->db->select( $table, ["rowid"], $props )->hash;

    if ($rcd) {
        
        $self->dbh->db->update( $table, $update, { rowid => $rcd->{'rowid'} } ) if ($update);

        return $rcd->{'rowid'};
    }

    return $self->dbh->db->insert( $table, { %$props, %$update } )->last_insert_id;

}

=item insert( $table, $properties )

This function will insert the record into the designated table.

@returns: (int) record_id

=cut

sub insert {
    my ( $self, $table, $props ) = @_;

    return $self->dbh->db->insert( $table, $props )->last_insert_id;
}

=item query( $sql )

This function will insert the record into the designated table.

@returns: (int) record_id

=cut

sub query {
    my ( $self, $sql ) = @_;

    return $self->dbh->db->query($sql);
}

=item delete( $table, $properties )

This function will delete the record from the designated table.

@returns: (int) record_id

=cut

sub delete {
    my ( $self, $table, $props ) = @_;

    return $self->dbh->db->delete( $table, $props );
}

=item exists( $table, $properties )

This function will check if the record exists in the designated table.

@returns: (int) [1|0]

=cut

sub exists {
    my ( $self, $table, $props ) = @_;

    return ( $self->dbh->db->select( $table, ['rowid'], $props )->hash )
      ? 1
      : 0;
}

=item modified( $table, $properties )

This function will check if the record exists in the designated table.

@returns: (int) [1|0]

=cut

sub modified {
    my ( $self, $table, $props ) = @_;

    return ( $self->dbh->db->select( $table, ['rowid'], $props )->hash )
      ? 1
      : 0;
}

1;

__DATA__
@@ migrations
-- 1 up
CREATE TABLE articles ( link VARCHAR(255) NOT NULL UNIQUE, title TEXT, teaser TEXT, modified INTEGER, published VARCHAR(35), author INTEGER, type VARCHAR(255), lang VARCHAR(3) );
-- 1 down
DROP TABLE articles;
-- 2 up
CREATE TABLE tags ( id VARCHAR(255), en VARCHAR(255), fr VARCHAR(255), iu VARCHAR(255) );
-- 2 down
DROP TABLE tags;
-- 3 up
CREATE TABLE article_tag ( article_id INTEGER, tag_id INTEGER );
-- 3 down
DROP TABLE article_tag;
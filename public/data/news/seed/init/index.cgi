#!/usr/bin/env perl
use common::sense;

use File::Spec;
use lib join( '/', substr( File::Spec->rel2abs($0), 0, rindex( File::Spec->rel2abs($0), '/public/' ) ), 'cgi-lib' );

use cPanelUserConfig;
use Prism;
use JSON::MaybeXS;
use Path::Tiny qw/path/;
use SQL::Abstract;
use DBI;
# enable hires wallclock timing if possible
use Benchmark ':hireswallclock';

use Data::Dmp qw/dd dmp/;

# =================
# = PREPROCESSING =
# =================
my $prism = Prism->new( 'index.yml' );

my $t0 = Benchmark->new;

my $dbh = DBI->connect(
        'dbi:SQLite:dbname='.$prism->closest( 'public' )->sibling( $prism->get('database.path') )->stringify,
        $prism->get('database.username'), $prism->get('database.password'),
        { RaiseError => 0, AutoCommit => 1, PrintError => 0 }
    );

my ( $cache, $queries )  = ( {}, {
'article' => $dbh->prepare( 'INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?)'),
'department' => $dbh->prepare( 'INSERT OR REPLACE INTO departments VALUES (?, ?, ?)'),
'minister' => $dbh->prepare( 'INSERT OR REPLACE INTO ministers VALUES (?, ?, ?)'),
'type' => $dbh->prepare( 'INSERT OR REPLACE INTO types VALUES (?, ?, ?)'),
'pivot_department' => $dbh->prepare( 'INSERT INTO article_department VALUES (?, ?)'),
'pivot_minister' => $dbh->prepare( 'INSERT INTO article_minister VALUES (?, ?)'),
'pivot_type' => $dbh->prepare( 'INSERT INTO article_type VALUES (?, ?)')
});

while ( my $resource = $prism->next() )
{
    my ( $uri, $saveas, $lang ) =  ( delete $resource->{'uri'}, delete $resource->{'source'}, $resource->{'lang'} );
    
    my $json = decode_json( validate( $prism->download( $uri, $saveas )->slurp ) );
    
    foreach my $record ( @{ $json } )
    {
      my ( $department, $minister, $type  ) = map { consume( $_, $lang, delete $record->{ $_ } )  } ( 'department', 'minister', 'type' );
     
      my $record = $prism->map( $record, $resource );
      
      $queries->{'article'}->execute(  map { $record->{$_} } ('id', 'url', 'released', 'title', 'teaser', 'lang' ) );
      
      for ( @{ $department })
      {
          $queries->{'pivot_department'}->execute( $record->{'id'}, $_ ) unless has( 'department', $record->{'id'}, $_ );
      }
      
      for ( @{ $minister }) 
      {
          $queries->{'pivot_minister'}->execute( $record->{'id'}, $_ ) unless has( 'minister', $record->{'id'}, $_ );
      }
    
      for ( @{ $type }) 
      {

           $queries->{'pivot_type'}->execute( $record->{'id'}, $_ ) unless ( has( 'type', $record->{'id'}, $_ ) );
      }
      
      say " [indexed] ".$record->{'url'};
    
    }
}

my $t1 = Benchmark->new;

my $td = timediff($t1, $t0);
say "the code took:",timestr($td);

# ====================
# = HELPER FUNCTIONS =
# ====================


sub consume
{
    my ( $type, $lang, $data ) = @_;
    
    my $query = $queries ->{$type};
    my @entries;
    
    foreach my $key ( keys %{ $data } )
    {
    
       $cache->{$type}->{$key} = { 'en' => '' , 'fr' => '' } if ( ! exists $cache->{$type}->{$key} );
       $cache->{$type}->{$key}->{$lang} = $data->{$key};
       push( @entries, [ $key, $cache->{$type}->{$key}->{'en'}, $cache->{$type}->{$key}->{'fr'} ] );
    }
    
    $query->execute( @{$_} ) for @entries;
    
    return [ map { $_->[0] } @entries ];
}

sub has
{
    my ( $type, $article, $other ) = @_;
    return ($dbh->selectrow_array( "SELECT * FROM article_$type WHERE article_id = '$article' AND ".$type."_id = '$other' LIMIT 1" ) ) ? 1 : 0; 
}


sub validate
{
    my $json = shift;
    # lets clean up the end of the string;
    
    $json =~ s/,\s*\]\s*$/]/si;
    
    return $json;
}

/* Initial Table */
CREATE TABLE articles (
  id VARCHAR(64) PRIMARY KEY,
  link VARCHAR(255),
  pubdate INTEGER,
  title TEXT,
  teaser TEXT,
  lang  VARCHAR(3)   
)
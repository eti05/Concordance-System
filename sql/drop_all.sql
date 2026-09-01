-- Deletes all database objects created by the Concordance System.
-- Used when we want to reset the database.

BEGIN

  -- Delete the views.
  FOR current_view IN (
    SELECT view_name
    FROM user_views
    WHERE view_name IN (
      'V_WORD_INDEX',
      'V_DOCUMENT_STATS',
      'V_GROUP_STATS'
    )
  ) LOOP
    EXECUTE IMMEDIATE 'DROP VIEW ' || current_view.view_name;
  END LOOP;


  -- Delete the tables.
  FOR current_table IN (
    SELECT table_name
    FROM user_tables
    WHERE table_name IN (
      'PHRASEWORDS',
      'PHRASES',
      'GROUPMEMBERS',
      'GROUPS',
      'OCCURRENCES',
      'WORDS',
      'DOCUMENTS',
      'AUTHORS'
    )
  ) LOOP
    EXECUTE IMMEDIATE
      'DROP TABLE ' || current_table.table_name || ' CASCADE CONSTRAINTS';
  END LOOP;

END;
/
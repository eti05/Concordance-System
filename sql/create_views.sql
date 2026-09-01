-- Concordance System statistics.
-- These views calculate statistics from the existing data.


-- Statistics for each word.
CREATE OR REPLACE VIEW v_word_index AS
SELECT
    w.WordID,
    w.WordText,
    COUNT(o.OccID)          AS Occurrences,
    COUNT(DISTINCT o.DocID) AS Documents,
    LENGTH(w.WordText)      AS CharCount
FROM Words w
LEFT JOIN Occurrences o
    ON o.WordID = w.WordID
GROUP BY
    w.WordID,
    w.WordText;


-- Statistics for each document.
CREATE OR REPLACE VIEW v_document_stats AS
SELECT
    d.DocID,
    d.Title,

    -- Number of words in the document.
    COUNT(*) AS TotalWords,

    -- Number of different words.
    COUNT(DISTINCT o.WordID) AS UniqueWords,

    -- Number of paragraphs.
    MAX(o.ParagraphNum) AS Paragraphs,

    -- Average word length.
    ROUND(AVG(LENGTH(w.WordText)), 2) AS AvgWordLength

FROM Documents d
JOIN Occurrences o
    ON o.DocID = d.DocID
JOIN Words w
    ON w.WordID = o.WordID
GROUP BY
    d.DocID,
    d.Title;


-- Statistics for each word group.
CREATE OR REPLACE VIEW v_group_stats AS
SELECT
    g.GroupID,
    g.GroupName,

    -- Number of words in the group.
    COUNT(DISTINCT gm.WordID) AS WordCount,

    -- Total times these words appear.
    COUNT(o.OccID) AS TotalOccurrences,

    -- Number of documents that contain these words.
    COUNT(DISTINCT o.DocID) AS Documents

FROM Groups g
LEFT JOIN GroupMembers gm
    ON gm.GroupID = g.GroupID
LEFT JOIN Occurrences o
    ON o.WordID = gm.WordID
GROUP BY
    g.GroupID,
    g.GroupName;
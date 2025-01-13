# 索引失效

***description: 索引失效指的是查詢優化器無法使用或選擇不使用已經創建的索引，導致查詢效率下降***

### 1. 在索引列上使用函數或表達式

當在索引列上使用函數或進行運算時，索引通常會失效。

* 失效例子：`WHERE YEAR(date_column) = 2023`
* 有效替代：`WHERE date_column BETWEEN '2023-01-01' AND '2023-12-31'`

### 2. 隱式類型轉換

當條件中的資料類型與索引列不匹配時，可能導致隱式轉換，使索引失效。

* 失效例子：`WHERE string_id = 123` (string\_id 是字符串類型)
* 有效替代：`WHERE string_id = '123'`

### 3. 使用 NOT、!=、<> 操作符

這些操作符通常會導致索引失效，因為它們往往需要全表掃描。

* 失效例子：`WHERE indexed_column != 5`
* 優化建議：盡可能重寫為肯定形式的查詢

### 4. 使用 OR 條件連接不同的列

當 OR 連接的條件涉及不同的列時，可能會導致索引失效。

* 失效例子：`WHERE indexed_col1 = 5 OR indexed_col2 = 10`
* 優化建議：考慮使用 UNION 替代 OR

### 5. 使用 LIKE 進行前綴模糊查詢

以 '%' 開頭的 LIKE 查詢會使索引失效。

* 失效例子：`WHERE name LIKE '%John'`
* 有效例子：`WHERE name LIKE 'John%'`

### 6. 不滿足複合索引的最左前綴原則

對於複合索引，如果查詢條件不包含索引的第一列，可能導致索引失效。

* 索引：(col1, col2, col3)
* 失效例子：`WHERE col2 = 5 AND col3 = 10`
* 有效例子：`WHERE col1 = 1 AND col2 = 5 AND col3 = 10`

### 7. 範圍條件後的列失效

在複合索引中，範圍條件（如 >、<）後面的列會失效。

* 索引：(col1, col2, col3)
* 部分失效例子：`WHERE col1 = 5 AND col2 > 10 AND col3 = 15` (col3 的索引失效)

### 8. 資料分佈不均勻

當索引列的資料分佈極不均勻時，優化器可能選擇不使用索引。

* 例子：如果 90% 的行都是同一個值，對該值的查詢可能不會使用索引

### 9. 全表掃描更快時

當表很小或者查詢需要返回大部分資料時，全表掃描可能比使用索引更快。

### 10. 使用 IS NULL 或 IS NOT NULL

對於不接受 NULL 值的索引，IS NULL 條件會導致索引失效。

識別和解決索引失效問題是提高查詢性能的關鍵步驟。使用 EXPLAIN 命令可以幫助診斷索引使用情況。

這個概述涵蓋了 MySQL 中常見的索引失效情況。以下是一些額外的說明和實際應用的建議：

1.  診斷工具： 使用 EXPLAIN 命令是診斷索引使用情況的主要工具。例如：

    ```sql
    EXPLAIN SELECT * FROM users WHERE name LIKE '%Roy%';

    ```

    如果結果中 `type` 列顯示 `ALL`，通常意味著進行了全表掃描，索引可能失效。
2.  重寫查詢： 有時候，重寫查詢可以避免索引失效。例如，將 OR 改為 UNION：

    ```sql
    SELECT * FROM table WHERE col1 = 5 OR col2 = 10;

    ```

    可以改寫為：

    ```sql
    SELECT * FROM table WHERE col1 = 5
    UNION
    SELECT * FROM table WHERE col2 = 10;

    ```
3.  優化器提示： 在某些情況下，可以使用優化器提示來強制使用特定索引：

    ```sql
    SELECT /*+ INDEX(table index_name) */ * FROM table WHERE ...;

    ```
4.  統計信息更新： 確保表的統計信息是最新的，可以幫助優化器做出更好的決策：

    ```sql
    ANALYZE TABLE table_name;

    ```
5.  索引設計： 根據實際查詢模式設計索引。例如，如果經常需要按日期範圍和狀態查詢，可以創建複合索引：

    ```sql
    CREATE INDEX idx_date_status ON table(date, status);

    ```
6.  監控和維護： 定期檢查慢查詢日誌，識別可能的索引失效問題：

    ```sql
    SHOW VARIABLES LIKE 'slow_query_log';
    SHOW VARIABLES LIKE 'long_query_time';

    ```
7. 避免過度索引： 雖然索引可以提高查詢速度，但過多的索引會影響插入和更新性能，並增加維護成本。
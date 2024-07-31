from datetime import datetime
import oracledb
import config
import array
import os

## -- log ------------------------------------------------------------------

def log(s):
   dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
   print( "["+dt+"] "+ str(s), flush=True)


## -- longhand ------------------------------------------------------------------

def longhand(key, abbreviations):
    if key in abbreviations:
        return abbreviations[key]
    else:
        return key

## -- dictString ------------------------------------------------------------

def dictString(d,key):
   value = d.get(key)
   if value is None:
       return "-"
   else:
       return value  
   
# -- insert in APEX database ----------------------------------------------------

def apexInsertSubDocs( connection, sub_docs ):
    log("<apexInsertSubDocs>")
    if len(sub_docs) == 0: 
        return sub_docs;
    doc = sub_docs[0]

    UNIQUE_ID = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
    file_ext = os.path.splitext(doc.metadata["source"])[1].lower()
    content_type = longhand(file_ext
                            ,{'.pdf': 'application/pdf', '.txt': 'text/html'}
                           )
    content = ""
    for doc in sub_docs:
        content = content + doc.page_content

    result = {
        "filename": doc.metadata["source"],
        "date": UNIQUE_ID,
        "applicationName": "LangChain",
        "modified": UNIQUE_ID,
        "contentType": content_type,
        "creationDate": UNIQUE_ID,
        "content": content,
        "path": config.OBJECT_STORAGE_LINK+doc.metadata["source"]
    }
    deleteDoc( connection, result["path"])
    insertDocs( connection, result )
    for doc in sub_docs:
        doc.metadata["doc_id"] = str(int(result.get("docId")))
        doc.metadata["content_type"] = content_type
        doc.metadata["filename"] = dictString(result,"filename")
        doc.metadata["path"] = dictString(result,"path")
        if doc.metadata.get("page") is not None:
            doc.metadata["page"] = doc.metadata["page"]+1
    return sub_docs

# -- insertDocs -----------------------------------------------------------------

def insertDocs( dbConn, result ):  
    cur = dbConn.cursor()
    stmt = """
        INSERT INTO docs (
            application_name, author, translation, summary_embed, content, content_type,
            creation_date, modified, other1, other2, other3, parsed_by,
            filename, path, publisher, region, summary, source_type
        )
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17, :18)
        RETURNING id INTO :19
    """
    id_var = cur.var(oracledb.NUMBER)
    data = (
            dictString(result,"applicationName"), 
            dictString(result,"author"),
            dictString(result,"translation"),
            "", # array.array("f", result["summaryEmbed"]),
            dictString(result,"content"),
            dictString(result,"contentType"),
            dictString(result,"creationDate"),
            dictString(result,"modified"),
            dictString(result,"other1"),
            dictString(result,"other2"),
            dictString(result,"other3"),
            dictString(result,"parsed_by"),
            dictString(result,"filename"),
            dictString(result,"path"),
            dictString(result,"publisher"),
            "", # os.getenv("TF_VAR_region"),
            dictString(result,"summary"),
            dictString(result,"source_type"),
            id_var
        )
    try:
        cur.execute(stmt, data)
        # Get generated id
        id = id_var.getvalue()    
        log("<insertDocs> returning id=" + str(id[0]) )        
        result["docId"] = id[0]
        log(f"<insertDocs> Successfully inserted {cur.rowcount} records.")
    except (Exception) as error:
        log(f"<insertDocs> Error inserting records: {error}")
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()

# -- insertDocsChunck -----------------------------------------------------------------

def insertDocsChunck(result):  
    log("<langchain insertDocsChunck>")
    docs = [
        Document(
            page_content=dictString(result,"content"),
            metadata=
            {
                "doc_id": dictInt(result,"docId"), 
                "translation": dictString(result,"translation"), 
                "content_type": dictString(result,"contentType"),
                "filename": dictString(result,"filename"), 
                "path": dictString(result,"path"), 
                "region": os.getenv("TF_VAR_region"), 
                "summary": dictString(result,"summary"), 
                "page": dictInt(result,"page"), 
                "char_start": "1", 
                "char_end": "0" 
            },
        )
    ]
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)      
    docs_chunck = text_splitter.split_documents(docs)
    print( docs_chunck )
    vectorstore = OracleVS( client=dbConn, table_name="docs_langchain", embedding_function=embeddings, distance_strategy=DistanceStrategy.DOT_PRODUCT )
    vectorstore.add_documents( docs_chunck )
    log("</langchain insertDocsChunck>")

# -- deleteDoc -----------------------------------------------------------------

def deleteDoc(dbConn, path):
    cur = dbConn.cursor()
    log(f"<deleteDoc> path={path}")
    try:
        cur.execute("delete from docs where path=:1", (path,))
        print(f"<deleteDoc> Successfully {cur.rowcount} docs deleted")
    except (Exception) as error:
        print(f"<deleteDoc> Error deleting: {error}")
    finally:
        # Close the cursor and connection
        if cur:
            cur.close()

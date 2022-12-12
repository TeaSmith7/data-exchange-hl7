import gov.cdc.dex.hl7.MmgUtil
// import gov.cdc.hl7.HL7StaticParser

import org.junit.jupiter.api.Test

import kotlin.test.assertEquals
// import kotlin.test.assertTrue

import org.slf4j.LoggerFactory
// import java.util.*

// import gov.cdc.dex.redisModels.MMG
// import gov.cdc.dex.hl7.model.ConditionCode
import gov.cdc.dex.hl7.model.PhinDataType
// import gov.cdc.dex.redisModels.ValueSetConcept

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.google.gson.reflect.TypeToken

import  gov.cdc.dex.azure.RedisProxy
import gov.cdc.dex.hl7.TransformerSql

class MmgSqlTest {

    companion object {
        val REDIS_CACHE_NAME = System.getenv("REDIS_CACHE_NAME")
        val REDIS_PWD = System.getenv("REDIS_CACHE_KEY")
        val redisProxy = RedisProxy(REDIS_CACHE_NAME, REDIS_PWD)
        // val redisClient = redisProxy.getJedisClient()
        val logger = LoggerFactory.getLogger(MmgSqlTest::class.java.simpleName)
        private val gson = Gson()
        private val gsonWithNullsOn: Gson = GsonBuilder().serializeNulls().create() 

        const val MMG_BLOCK_TYPE_SINGLE = "Single"
    } // .companion 

    // @Test
    // fun testRedisInstanceUsed() {
    //     logger.info("testRedisInstanceUsed: REDIS_CACHE_NAME: --> ${REDIS_CACHE_NAME}")
    //     assertEquals(REDIS_CACHE_NAME, "tf-vocab-cache-dev.redis.cache.windows.net")
    // } // .testRedisInstanceUsed


    @Test
    fun testTransformerSql() {

        // MMGs for the message
        // ------------------------------------------------------------------------------
        val filePath = "/TBRD_V1.0.2_TM_TC04.hl7"
        val testMsg = this::class.java.getResource(filePath).readText()
        val mmgUtil = MmgUtil(redisProxy)
        val mmgsArr = mmgUtil.getMMGFromMessage(testMsg, filePath, "")
        assertEquals(mmgsArr.size, 2)

        // Default Phin Profiles Types
        // ------------------------------------------------------------------------------
        val dataTypesFilePath = "/DefaultFieldsProfileX.json"
        val dataTypesMapJson = this::class.java.getResource(dataTypesFilePath).readText()
        // val dataTypesMapJson = this::class.java.classLoader.getResource(dataTypesFilePath).readText()

        // val dataTypesMap = Map<String, List<PhinDataType>>
        val dataTypesMapType = object : TypeToken< Map<String, List<PhinDataType>> >() {}.type
        val profilesMap: Map<String, List<PhinDataType>> = gson.fromJson(dataTypesMapJson, dataTypesMapType)


        // MMG Based Model for the message
        // ------------------------------------------------------------------------------
        val mmgBasedModelPath = "/model.json"
        val mmgBasedModelStr = this::class.java.getResource(mmgBasedModelPath).readText()
        // logger.info("mmgBasedModelStr: --> ${mmgBasedModelStr}")


        // Transformer SQL
        // ------------------------------------------------------------------------------
        val transformer = TransformerSql()

        val mmgs = transformer.getMmgsFiltered(mmgsArr)
        val mmgBlocks = mmgs.flatMap { it.blocks } // .mmgBlocks
        val (mmgBlocksSingle, _) = mmgBlocks.partition { it.type == MMG_BLOCK_TYPE_SINGLE }
        val mmgElemsBlocksSingleNonRepeats = mmgBlocksSingle.flatMap { it.elements }.filter{ !it.isRepeat }


        val singlesNonRepeatsModel = transformer.singlesNonRepeatstoSqlModel(mmgElemsBlocksSingleNonRepeats, profilesMap, mmgBasedModelStr)
        logger.info(" singlesNonRepeatsModel: --> \n\n${gsonWithNullsOn.toJson(singlesNonRepeatsModel)}\n")      


    } // .testRedisInstanceUsed


} // .MmgSqlTest




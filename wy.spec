grammar wenyan;
program                     : statement* ;
statement                   : declare_statement
                            | define_statement
                            | print_statement
                            | for_statement
                            | function_statement
                            | if_statement
                            | try_statement
                            | throw_statement
                            | return_statement
                            | math_statement
                            | not_statement
                            | assign_statement
                            | import_statement
                            | object_statement
                            | expr_statement
                            | name_statement
                            | array_statement
                            | discard_statement
                            | take_statement
                            | CONTINUE
                            | BREAK
                            | comment
                            | macro_statement;

declare_statement           : ('吾有'|'今有') INT_NUM TYPE ('曰' value)* ;
define_statement            : (declare_statement name_multi_statement)|init_define_statement ;
name_single_statement       : '名之曰' IDENTIFIER ;
name_multi_statement        : name_single_statement ('曰' IDENTIFIER)* ;
name_statement              : name_multi_statement ;
init_define_statement       : '有' TYPE value (name_single_statement)? ;

print_statement             : '書之' ;
discard_statement           : '噫' ;
take_statement              : '取' (INT_NUM|REST) ;

function_statement          : function_define_statement|function_call_statement ;
function_call_statement     : function_pre_call|function_post_call ;
function_pre_call           : '施' value ('於' value)* ;
function_post_call          : '以施' value ;
function_define_statement   : ('吾有'|'今有') INT_NUM '術' name_single_statement
                              '欲行是術' ('必先得' function_param_groups)?
                              ('是術曰'|'乃行是術曰') statement* '是謂' IDENTIFIER '之術也' ;
function_param_groups       : (function_param_group+ (function_rest_param_group)?
                            | function_rest_param_group) ;
function_param_group        : INT_NUM TYPE ('曰' IDENTIFIER)+ ;
function_rest_param_group   : REST TYPE '曰' IDENTIFIER ;

if_statement                : if_clause (elseif_clause)* (else_clause)? IF_END ;
if_clause                   : IF if_expression '者' statement*
                            | IF_TRUE statement*
                            | IF_FALSE statement* ;
elseif_clause               : ELSEIF if_expression '者' statement* ;
else_clause                 : ELSE statement* ;
if_expression               : if_atom ((IF_LOGIC_OP|LOGIC_BINARY_OP) if_atom)* ;
if_atom                     : value (SUBSCRIPT subscript_index | LENGTH)? ;

try_statement               : TRY_START statement* TRY_CATCH try_catch_clause* TRY_END ;
try_catch_clause            : try_catch_error_clause|try_catch_all_clause ;
try_catch_error_clause      : TRY_CATCH_ERR0 value TRY_CATCH_ERR1 name_single_statement? statement* ;
try_catch_all_clause        : TRY_CATCH_ALL name_single_statement? statement* ;
throw_statement             : THROW_START value THROW_END ('曰' value)? ;

for_statement               : for_arr_statement
                            | for_enum_statement
                            | for_while_statement ;
for_arr_statement           : FOR_START_ARR value FOR_MID_ARR IDENTIFIER statement* IF_END ;
for_enum_statement          : FOR_START_ENUM value FOR_MID_ENUM statement* IF_END ;
for_while_statement         : FOR_START_WHILE statement* IF_END ;

math_statement              : arith_math_statement|mod_math_statement ;
arith_math_statement        : ARITH_BINARY_OP value preposition value ;
mod_math_statement          : '除' value preposition value POST_MOD_MATH_OP ;
not_statement               : UNARY_OP value ;

assign_statement            : '昔之' assign_target '者' '今' assign_value assign_rhs_subscript? ('是'|'是矣'|'是也')
                            | '昔之' assign_target '者' '今' ASSIGN_DELETE ('是也')? ;
assign_target               : IDENTIFIER (SUBSCRIPT subscript_index)? ;
assign_value                : value ;
assign_rhs_subscript        : SUBSCRIPT subscript_index ;

import_statement            : '吾嘗觀' import_path '之書' ('方悟' IDENTIFIER+ '之義')? ;
import_path                 : import_segment ('中' import_segment)* ;
import_segment              : STRING_LITERAL|IDENTIFIER ;

object_statement            : ('吾有'|'今有') INT_NUM '物' name_multi_statement (object_define_statement)? ;
object_define_statement     : '其物如是' object_prop+ '是謂' IDENTIFIER '之物也' ;
object_prop                 : '物之' STRING_LITERAL '者' TYPE '曰' value ;

array_statement             : array_cat_statement|array_push_statement ;
array_cat_statement         : '銜' value (PREPOSITION_RIGHT value)+ ;
array_push_statement        : '充' value (PREPOSITION_RIGHT value)+ ;

expr_statement              : '夫' value
                            | '夫' value SUBSCRIPT subscript_index
                            | '夫' value LENGTH
                            | '夫' value value LOGIC_BINARY_OP ;

return_statement            : '乃得' value|'乃歸空無'|'乃得矣' ;

value                       : data|'其' ;
data                        : STRING_LITERAL|BOOL_VALUE|IDENTIFIER|INT_NUM|FLOAT_NUM ;
subscript_index             : value|REST ;

STRING_LITERAL              : '「「' ( ~('」') )* '」」'
                            | '『' ( ~('』') )* '』' ;
IDENTIFIER                  : '「' ( ~('」') )+ '」' ;
ARITH_BINARY_OP             : '加'|'減'|'乘'|'除' ;
LOGIC_BINARY_OP             : '中有陽乎'|'中無陰乎' ;
POST_MOD_MATH_OP            : '所餘幾何' ;
UNARY_OP                    : '變' ;
preposition                 : PREPOSITION_LEFT|PREPOSITION_RIGHT ;
PREPOSITION_LEFT            : '於' ;
PREPOSITION_RIGHT           : '以' ;
IF                          : '若' ;
ELSE                        : '若非' ;
ELSEIF                      : '或若' ;
IF_TRUE                     : '若其然者' ;
IF_FALSE                    : '若其不然者' ;
IF_LOGIC_OP                 : '等於'|'不等於'|'不大於'|'不小於'|'大於'|'小於' ;
TRY_START                   : '姑妄行此' ;
TRY_CATCH                   : '如事不諧' ;
TRY_CATCH_ERR0              : '豈' ;
TRY_CATCH_ERR1              : '之禍歟' ;
TRY_CATCH_ALL               : '不知何禍歟' ;
TRY_END                     : '乃作罷' ;
THROW_START                 : '嗚呼' ;
THROW_END                   : '之禍' ;
FOR_START_ARR               : '凡' ;
FOR_START_ENUM              : '為是' ;
FOR_START_WHILE             : '恆為是' ;
FOR_MID_ARR                 : '中之' ;
FOR_MID_ENUM                : '遍' ;
IF_END                      : '云云'|'也' ;
FLOAT_NUM                   : INT_NUM '又' (INT_NUM FLOAT_NUM_KEYWORDS)+ ;
FLOAT_NUM_KEYWORDS          : '分'|'釐'|'毫'|'絲'|'忽'|'微'|'纖'|'沙'|'塵'|'埃'|'渺'|'漠' ;
INT_NUM                     : INT_NUM_KEYWORDS+ ;
INT_NUM_KEYWORDS            : '負'|'·'|'零'|'〇'|'一'|'二'|'三'|'四'|'五'|'六'|'七'|'八'|'九'|'十'|'百'|'千'|'萬'|'億'|'兆'|'京'|'垓'|'秭'|'穣'|'溝'|'澗'|'正'|'載'|'極' ;
TYPE                        : '數'|'列'|'言'|'爻'|'物'|'元' ;
BOOL_VALUE                  : '陰'|'陽' ;
LENGTH                      : '之長' ;
SUBSCRIPT                   : '之' ;
REST                        : '其餘' ;
CONTINUE                    : '乃止是遍' ;
ASSIGN_DELETE               : '不復存矣' ;
macro_statement             : MACRO_FROM macro_literal MACRO_TO macro_literal ;
macro_literal               : STRING_LITERAL|IDENTIFIER ;
MACRO_FROM                  : '或云' ;
MACRO_TO                    : '蓋謂' ;
WS                          : ([ \t\r\n]|'　'|'。'|'、'|'，'|'矣')+ -> skip ;
comment                     : ('注曰'|'疏曰'|'批曰') STRING_LITERAL ;
BREAK                       : '乃止' ;

from __future__ import annotations

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from lib import db


# =========================
# Seed data (expanded)
# - mix of Chinese home cooking, high-protein fitness meals, and simple western dishes
# - "seasoning" items are frequently used as optional=1 in recipe_ingredients
# =========================

ITEMS = [{'name': '鸡蛋', 'category': 'protein', 'default_unit': 'pcs', 'shelf_life_days_default': 10},
 {'name': '牛奶', 'category': 'dairy', 'default_unit': 'ml', 'shelf_life_days_default': 7},
 {'name': '酸奶', 'category': 'dairy', 'default_unit': 'ml', 'shelf_life_days_default': 7},
 {'name': '奶酪', 'category': 'dairy', 'default_unit': 'g', 'shelf_life_days_default': 14},
 {'name': '黄油', 'category': 'dairy', 'default_unit': 'g', 'shelf_life_days_default': 30},
 {'name': '淡奶油', 'category': 'dairy', 'default_unit': 'ml', 'shelf_life_days_default': 10},
 {'name': '鸡胸', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '鸡腿', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '猪里脊', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '牛肉片', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '虾仁', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 3},
 {'name': '三文鱼', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 3},
 {'name': '培根', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 10},
 {'name': '豆腐', 'category': 'protein', 'default_unit': 'g', 'shelf_life_days_default': 5},
 {'name': '大米', 'category': 'staple', 'default_unit': 'g', 'shelf_life_days_default': 180},
 {'name': '面条', 'category': 'staple', 'default_unit': 'g', 'shelf_life_days_default': 120},
 {'name': '意面', 'category': 'staple', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '燕麦', 'category': 'staple', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '面包', 'category': 'staple', 'default_unit': 'pcs', 'shelf_life_days_default': 5},
 {'name': '玉米粒', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 7},
 {'name': '番茄', 'category': 'vegetable', 'default_unit': 'pcs', 'shelf_life_days_default': 5},
 {'name': '蘑菇', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '金针菇', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '洋葱', 'category': 'vegetable', 'default_unit': 'pcs', 'shelf_life_days_default': 10},
 {'name': '土豆', 'category': 'vegetable', 'default_unit': 'pcs', 'shelf_life_days_default': 20},
 {'name': '胡萝卜', 'category': 'vegetable', 'default_unit': 'pcs', 'shelf_life_days_default': 14},
 {'name': '生菜', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 5},
 {'name': '菠菜', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 5},
 {'name': '西兰花', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 7},
 {'name': '青椒', 'category': 'vegetable', 'default_unit': 'pcs', 'shelf_life_days_default': 7},
 {'name': '黄瓜', 'category': 'vegetable', 'default_unit': 'pcs', 'shelf_life_days_default': 7},
 {'name': '茄子', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 7},
 {'name': '西葫芦', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 7},
 {'name': '豆芽', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 4},
 {'name': '葱', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 7},
 {'name': '姜', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 14},
 {'name': '蒜', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 14},
 {'name': '香菜', 'category': 'vegetable', 'default_unit': 'g', 'shelf_life_days_default': 5},
 {'name': '紫菜', 'category': 'staple', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '海带', 'category': 'staple', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '柠檬', 'category': 'fruit', 'default_unit': 'pcs', 'shelf_life_days_default': 14},
 {'name': '苹果', 'category': 'fruit', 'default_unit': 'pcs', 'shelf_life_days_default': 20},
 {'name': '香蕉', 'category': 'fruit', 'default_unit': 'pcs', 'shelf_life_days_default': 7},
 {'name': '盐', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '糖', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '生抽', 'category': 'seasoning', 'default_unit': 'ml', 'shelf_life_days_default': 3650},
 {'name': '老抽', 'category': 'seasoning', 'default_unit': 'ml', 'shelf_life_days_default': 3650},
 {'name': '醋', 'category': 'seasoning', 'default_unit': 'ml', 'shelf_life_days_default': 3650},
 {'name': '蚝油', 'category': 'seasoning', 'default_unit': 'ml', 'shelf_life_days_default': 3650},
 {'name': '料酒', 'category': 'seasoning', 'default_unit': 'ml', 'shelf_life_days_default': 3650},
 {'name': '黑胡椒', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '辣椒粉', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '淀粉', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '孜然粉', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '芝麻', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '花生', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '蜂蜜', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 365},
 {'name': '番茄酱', 'category': 'seasoning', 'default_unit': 'g', 'shelf_life_days_default': 3650},
 {'name': '食用油', 'category': 'seasoning', 'default_unit': 'ml', 'shelf_life_days_default': 3650},
 {'name': '咖喱块', 'category': 'seasoning', 'default_unit': 'pcs', 'shelf_life_days_default': 3650}]

RECIPES = [{'name': '蛋炒饭', 'tags': 'rice,quick,stirfry', 'allergens': 'egg', 'steps': '先炒散鸡蛋，加入洋葱翻炒；下米饭炒匀调味。', 'nutrition': {'calories': 520}},
 {'name': '番茄炒蛋', 'tags': 'egg,quick,home', 'allergens': 'egg', 'steps': '番茄炒出汁后倒入蛋液；凝固后翻炒调味。', 'nutrition': {'calories': 320}},
 {'name': '鸡胸沙拉', 'tags': 'salad,protein,light', 'allergens': '', 'steps': '鸡胸煎/煮熟切片；与生菜番茄黄瓜拌匀，挤柠檬。', 'nutrition': {'calories': 280}},
 {'name': '蔬菜沙拉', 'tags': 'salad,light', 'allergens': '', 'steps': '生菜番茄黄瓜胡萝卜切好拌匀，少量盐/醋调味。', 'nutrition': {'calories': 200}},
 {'name': '蘑菇汤', 'tags': 'soup,western', 'allergens': 'dairy', 'steps': '黄油炒香洋葱蘑菇；加牛奶/水煮5分钟，调味。', 'nutrition': {'calories': 220}},
 {'name': '洋葱土豆炖鸡', 'tags': 'stew,home,protein', 'allergens': 'soy', 'steps': '鸡肉煎香后加洋葱土豆；少量料酒生抽，小火炖至软。', 'nutrition': {'calories': 450}},
 {'name': '牛奶燕麦', 'tags': 'breakfast,quick', 'allergens': 'dairy', 'steps': '牛奶加热后下燕麦煮3-5分钟，按喜好加蜂蜜。', 'nutrition': {'calories': 330}},
 {'name': '酸奶水果碗', 'tags': 'breakfast,no_cook,light', 'allergens': 'dairy', 'steps': '酸奶打底，加水果片；撒燕麦淋蜂蜜即可。', 'nutrition': {'calories': 380}},
 {'name': '炒面',
  'tags': 'noodle,stirfry,quick',
  'allergens': 'gluten,soy',
  'steps': '面条煮熟过冷水；与蔬菜大火翻炒，少量生抽调味。',
  'nutrition': {'calories': 480}},
 {'name': '番茄拌面', 'tags': 'noodle,quick', 'allergens': 'gluten,soy', 'steps': '番茄炒出汁；拌入煮熟面条，蒜末提香。', 'nutrition': {'calories': 430}},
 {'name': '青椒土豆丝', 'tags': 'vegetable,stirfry,home', 'allergens': '', 'steps': '土豆切丝泡水；与青椒蒜末快炒，少量醋提味。', 'nutrition': {'calories': 260}},
 {'name': '西兰花虾仁',
  'tags': 'protein,stirfry,fit',
  'allergens': 'shellfish,soy',
  'steps': '西兰花焯水；虾仁与蒜末快炒后合炒，少量生抽。',
  'nutrition': {'calories': 350}},
 {'name': '蒜蓉西兰花', 'tags': 'vegetable,quick', 'allergens': '', 'steps': '西兰花焯水；蒜蓉爆香后合炒，少量盐。', 'nutrition': {'calories': 180}},
 {'name': '菠菜豆腐汤', 'tags': 'soup,light', 'allergens': 'soy', 'steps': '水开下豆腐煮3分钟；加入菠菜烫熟，调味。', 'nutrition': {'calories': 190}},
 {'name': '麻婆豆腐(简)', 'tags': 'home,spicy,protein', 'allergens': 'soy', 'steps': '牛肉末/片炒香；下豆腐与调料小火煮，淀粉勾芡。', 'nutrition': {'calories': 420}},
 {'name': '番茄豆腐煲', 'tags': 'home,light', 'allergens': 'soy', 'steps': '番茄炒出汁；加入豆腐焖煮5分钟，少量生抽。', 'nutrition': {'calories': 300}},
 {'name': '黑胡椒鸡胸', 'tags': 'protein,fit,quick', 'allergens': '', 'steps': '鸡胸拍松撒黑胡椒盐；平底锅两面煎熟。', 'nutrition': {'calories': 320}},
 {'name': '孜然鸡胸', 'tags': 'protein,fit,quick', 'allergens': '', 'steps': '鸡胸切片加孜然盐腌10分钟；大火快煎。', 'nutrition': {'calories': 330}},
 {'name': '鸡胸西兰花饭', 'tags': 'fit,protein,rice', 'allergens': 'soy', 'steps': '鸡胸煎熟；西兰花焯水；配米饭与少量生抽。', 'nutrition': {'calories': 520}},
 {'name': '牛肉洋葱炒饭', 'tags': 'rice,protein', 'allergens': 'soy', 'steps': '洋葱牛肉炒香；加入米饭翻炒，少量生抽调味。', 'nutrition': {'calories': 580}},
 {'name': '猪里脊青椒', 'tags': 'home,protein,stirfry', 'allergens': 'soy', 'steps': '里脊切丝上浆；与青椒快炒，生抽调味。', 'nutrition': {'calories': 480}},
 {'name': '番茄牛肉汤', 'tags': 'soup,home,protein', 'allergens': '', 'steps': '番茄洋葱炒香；加水煮开后下牛肉片煮熟调味。', 'nutrition': {'calories': 420}},
 {'name': '咖喱鸡腿土豆', 'tags': 'curry,stew,home', 'allergens': '', 'steps': '鸡腿煎香；加入洋葱土豆胡萝卜加水煮熟，放咖喱块融化。', 'nutrition': {'calories': 650}},
 {'name': '煎三文鱼沙拉', 'tags': 'salad,protein,omega3', 'allergens': 'fish', 'steps': '三文鱼煎至熟；与生菜黄瓜拌匀，挤柠檬少量盐。', 'nutrition': {'calories': 520}},
 {'name': '培根蘑菇意面', 'tags': 'pasta,western', 'allergens': 'dairy,gluten', 'steps': '意面煮熟；培根蘑菇炒香，加淡奶油收汁拌面。', 'nutrition': {'calories': 760}},
 {'name': '番茄意面', 'tags': 'pasta,quick', 'allergens': 'gluten', 'steps': '番茄炒成酱；加番茄酱调味后拌入意面。', 'nutrition': {'calories': 620}},
 {'name': '奶油蘑菇意面', 'tags': 'pasta,western', 'allergens': 'dairy,gluten', 'steps': '蘑菇黄油炒香；加淡奶油煮至浓稠，拌意面。', 'nutrition': {'calories': 720}},
 {'name': '烤土豆块', 'tags': 'snack,oven,quick', 'allergens': '', 'steps': '土豆切块拌油盐黑胡椒；烤/空气炸至金黄。', 'nutrition': {'calories': 320}},
 {'name': '西葫芦炒蛋', 'tags': 'egg,quick,home', 'allergens': 'egg', 'steps': '西葫芦片炒软；倒入蛋液炒至凝固调味。', 'nutrition': {'calories': 300}},
 {'name': '茄子烧豆腐', 'tags': 'home,vegetable', 'allergens': 'soy', 'steps': '茄子煎软后加豆腐；少量生抽焖煮入味。', 'nutrition': {'calories': 430}},
 {'name': '黄瓜拌豆腐', 'tags': 'cold,quick,light', 'allergens': 'soy', 'steps': '豆腐切块；黄瓜拍碎，加入醋盐拌匀。', 'nutrition': {'calories': 220}},
 {'name': '紫菜蛋花汤', 'tags': 'soup,quick', 'allergens': 'egg', 'steps': '水开下紫菜；淋入蛋液成蛋花，调味即可。', 'nutrition': {'calories': 120}},
 {'name': '海带豆腐汤', 'tags': 'soup,light', 'allergens': 'soy', 'steps': '海带泡发煮开；下豆腐煮3分钟，调味。', 'nutrition': {'calories': 160}},
 {'name': '豆芽炒面', 'tags': 'noodle,quick', 'allergens': 'gluten,soy', 'steps': '面条煮熟；与豆芽大火翻炒，生抽调味。', 'nutrition': {'calories': 450}},
 {'name': '金针菇肥牛卷', 'tags': 'hotpot,protein', 'allergens': 'soy', 'steps': '金针菇用肥牛包裹；煮/煎熟后用生抽蘸食。', 'nutrition': {'calories': 520}},
 {'name': '鸡蛋三明治', 'tags': 'breakfast,quick', 'allergens': 'egg,gluten', 'steps': '煎蛋夹面包；加生菜番茄更清爽。', 'nutrition': {'calories': 420}},
 {'name': '奶酪鸡胸卷', 'tags': 'protein,western,fit', 'allergens': 'dairy', 'steps': '鸡胸煎熟卷入奶酪与生菜，静置融化切段。', 'nutrition': {'calories': 430}},
 {'name': '西兰花鸡蛋杯', 'tags': 'baked,egg,quick', 'allergens': 'dairy,egg', 'steps': '鸡蛋打散拌碎西兰花；入烤箱/空气炸定型。', 'nutrition': {'calories': 260}},
 {'name': '花生拌菠菜', 'tags': 'cold,home', 'allergens': 'peanut', 'steps': '菠菜焯水沥干；拌花生与少量醋。', 'nutrition': {'calories': 260}},
 {'name': '葱姜蒸鸡腿', 'tags': 'home,protein,steam', 'allergens': '', 'steps': '鸡腿加葱姜料酒腌片刻；蒸熟后调味。', 'nutrition': {'calories': 520}}]

# recipe_name -> list of tuples:
#   (item_name, qty, unit) or (item_name, qty, unit, optional_flag)
RECIPE_INGREDIENTS = {'蛋炒饭': [('鸡蛋', 2, 'pcs'), ('大米', 150, 'g'), ('洋葱', 0.5, 'pcs'), ('食用油', 10, 'ml', 1), ('盐', 2, 'g', 1)],
 '番茄炒蛋': [('鸡蛋', 2, 'pcs'), ('番茄', 2, 'pcs'), ('洋葱', 0.3, 'pcs'), ('食用油', 10, 'ml', 1), ('盐', 2, 'g', 1)],
 '鸡胸沙拉': [('鸡胸', 200, 'g'), ('生菜', 120, 'g'), ('番茄', 1, 'pcs'), ('黄瓜', 0.5, 'pcs'), ('柠檬', 0.25, 'pcs', 1), ('盐', 1, 'g', 1)],
 '蔬菜沙拉': [('生菜', 150, 'g'), ('番茄', 1, 'pcs'), ('胡萝卜', 1, 'pcs'), ('黄瓜', 0.5, 'pcs'), ('盐', 1, 'g', 1)],
 '蘑菇汤': [('蘑菇', 150, 'g'), ('洋葱', 1, 'pcs'), ('牛奶', 200, 'ml'), ('黄油', 10, 'g', 1), ('盐', 2, 'g', 1)],
 '洋葱土豆炖鸡': [('鸡胸', 200, 'g'), ('土豆', 2, 'pcs'), ('洋葱', 1, 'pcs'), ('料酒', 10, 'ml', 1), ('生抽', 10, 'ml', 1)],
 '牛奶燕麦': [('牛奶', 250, 'ml'), ('燕麦', 50, 'g'), ('蜂蜜', 10, 'g', 1)],
 '酸奶水果碗': [('酸奶', 200, 'ml'), ('香蕉', 1, 'pcs'), ('苹果', 0.5, 'pcs'), ('燕麦', 20, 'g', 1), ('蜂蜜', 10, 'g', 1)],
 '炒面': [('面条', 200, 'g'), ('胡萝卜', 1, 'pcs'), ('洋葱', 0.5, 'pcs'), ('青椒', 0.5, 'pcs'), ('生抽', 10, 'ml', 1), ('食用油', 10, 'ml', 1)],
 '番茄拌面': [('面条', 200, 'g'), ('番茄', 2, 'pcs'), ('蒜', 5, 'g', 1), ('生抽', 10, 'ml', 1)],
 '青椒土豆丝': [('土豆', 2, 'pcs'), ('青椒', 1, 'pcs'), ('蒜', 5, 'g', 1), ('醋', 5, 'ml', 1), ('食用油', 10, 'ml', 1), ('盐', 2, 'g', 1)],
 '西兰花虾仁': [('西兰花', 200, 'g'), ('虾仁', 150, 'g'), ('蒜', 5, 'g', 1), ('生抽', 10, 'ml', 1), ('食用油', 10, 'ml', 1)],
 '蒜蓉西兰花': [('西兰花', 250, 'g'), ('蒜', 8, 'g', 1), ('食用油', 10, 'ml', 1), ('盐', 2, 'g', 1)],
 '菠菜豆腐汤': [('菠菜', 150, 'g'), ('豆腐', 200, 'g'), ('盐', 2, 'g', 1)],
 '麻婆豆腐(简)': [('豆腐', 300, 'g'), ('牛肉片', 80, 'g', 1), ('辣椒粉', 2, 'g', 1), ('生抽', 10, 'ml', 1), ('淀粉', 5, 'g', 1)],
 '番茄豆腐煲': [('番茄', 2, 'pcs'), ('豆腐', 300, 'g'), ('生抽', 10, 'ml', 1)],
 '黑胡椒鸡胸': [('鸡胸', 200, 'g'), ('黑胡椒', 2, 'g', 1), ('盐', 2, 'g', 1), ('食用油', 10, 'ml', 1)],
 '孜然鸡胸': [('鸡胸', 200, 'g'), ('孜然粉', 2, 'g', 1), ('盐', 2, 'g', 1), ('食用油', 10, 'ml', 1)],
 '鸡胸西兰花饭': [('鸡胸', 200, 'g'), ('西兰花', 150, 'g'), ('大米', 150, 'g'), ('生抽', 10, 'ml', 1)],
 '牛肉洋葱炒饭': [('牛肉片', 120, 'g'), ('洋葱', 0.5, 'pcs'), ('大米', 150, 'g'), ('生抽', 10, 'ml', 1)],
 '猪里脊青椒': [('猪里脊', 200, 'g'), ('青椒', 1, 'pcs'), ('生抽', 10, 'ml', 1), ('淀粉', 5, 'g', 1), ('食用油', 10, 'ml', 1)],
 '番茄牛肉汤': [('番茄', 2, 'pcs'), ('牛肉片', 150, 'g'), ('洋葱', 0.5, 'pcs'), ('盐', 2, 'g', 1)],
 '咖喱鸡腿土豆': [('鸡腿', 250, 'g'), ('土豆', 2, 'pcs'), ('胡萝卜', 1, 'pcs'), ('洋葱', 0.5, 'pcs'), ('咖喱块', 1, 'pcs', 1)],
 '煎三文鱼沙拉': [('三文鱼', 200, 'g'), ('生菜', 120, 'g'), ('黄瓜', 0.5, 'pcs'), ('柠檬', 0.25, 'pcs', 1), ('盐', 2, 'g', 1)],
 '培根蘑菇意面': [('意面', 180, 'g'), ('培根', 60, 'g'), ('蘑菇', 120, 'g'), ('淡奶油', 80, 'ml', 1), ('盐', 2, 'g', 1)],
 '番茄意面': [('意面', 180, 'g'), ('番茄', 2, 'pcs'), ('番茄酱', 20, 'g', 1), ('蒜', 5, 'g', 1)],
 '奶油蘑菇意面': [('意面', 180, 'g'), ('蘑菇', 150, 'g'), ('淡奶油', 100, 'ml', 1), ('黄油', 10, 'g', 1), ('盐', 2, 'g', 1)],
 '烤土豆块': [('土豆', 2, 'pcs'), ('黑胡椒', 2, 'g', 1), ('盐', 2, 'g', 1), ('食用油', 10, 'ml', 1)],
 '西葫芦炒蛋': [('西葫芦', 200, 'g'), ('鸡蛋', 2, 'pcs'), ('食用油', 10, 'ml', 1), ('盐', 2, 'g', 1)],
 '茄子烧豆腐': [('茄子', 250, 'g'), ('豆腐', 200, 'g'), ('生抽', 10, 'ml', 1), ('食用油', 10, 'ml', 1)],
 '黄瓜拌豆腐': [('豆腐', 200, 'g'), ('黄瓜', 1, 'pcs'), ('醋', 5, 'ml', 1), ('盐', 2, 'g', 1)],
 '紫菜蛋花汤': [('紫菜', 5, 'g'), ('鸡蛋', 1, 'pcs'), ('盐', 1, 'g', 1)],
 '海带豆腐汤': [('海带', 20, 'g'), ('豆腐', 200, 'g'), ('盐', 1, 'g', 1)],
 '豆芽炒面': [('面条', 180, 'g'), ('豆芽', 200, 'g'), ('生抽', 10, 'ml', 1), ('食用油', 10, 'ml', 1)],
 '金针菇肥牛卷': [('金针菇', 200, 'g'), ('牛肉片', 200, 'g'), ('生抽', 10, 'ml', 1)],
 '鸡蛋三明治': [('面包', 2, 'pcs'), ('鸡蛋', 2, 'pcs'), ('生菜', 30, 'g', 1), ('番茄', 0.5, 'pcs', 1)],
 '奶酪鸡胸卷': [('鸡胸', 200, 'g'), ('奶酪', 30, 'g', 1), ('生菜', 50, 'g', 1), ('盐', 2, 'g', 1)],
 '西兰花鸡蛋杯': [('鸡蛋', 2, 'pcs'), ('西兰花', 80, 'g'), ('奶酪', 20, 'g', 1)],
 '花生拌菠菜': [('菠菜', 200, 'g'), ('花生', 30, 'g', 1), ('醋', 5, 'ml', 1)],
 '葱姜蒸鸡腿': [('鸡腿', 300, 'g'), ('葱', 20, 'g', 1), ('姜', 10, 'g', 1), ('料酒', 10, 'ml', 1), ('盐', 2, 'g', 1)]}


def seed() -> None:
    db.init_db()

    if db.count_rows("items") == 0:
        db.insert_items(ITEMS)

    if db.count_rows("recipes") == 0:
        db.insert_recipes(RECIPES)

    items = {item["name"]: item for item in db.list_items()}
    recipes = {recipe["name"]: recipe for recipe in db.list_recipes()}

    if db.count_rows("recipe_ingredients") == 0:
        ingredients = []
        for recipe_name, ings in RECIPE_INGREDIENTS.items():
            if recipe_name not in recipes:
                raise KeyError(f"Recipe not found in DB after insert: {recipe_name}")

            recipe_id = recipes[recipe_name]["recipe_id"]

            for ing in ings:
                # allow (name, qty, unit) or (name, qty, unit, optional)
                if not isinstance(ing, (list, tuple)) or len(ing) < 3:
                    raise ValueError(f"Invalid ingredient spec for {recipe_name}: {ing}")

                item_name = ing[0]
                qty = ing[1]
                unit = ing[2]
                optional = bool(ing[3]) if len(ing) >= 4 else False

                if item_name not in items:
                    raise KeyError(f"Item not found in items table: {item_name} (used in recipe={recipe_name})")

                ingredients.append(
                    {
                        "recipe_id": recipe_id,
                        "item_id": items[item_name]["item_id"],
                        "quantity": qty,
                        "unit": unit,
                        "optional": optional,
                    }
                )

        db.insert_recipe_ingredients(ingredients)


if __name__ == "__main__":
    seed()
    print("Seed completed")

from bs4 import BeautifulSoup
import os
import copy
import random

def belongs_to_previous(tag, unique_blocks):
    
    if len(unique_blocks) == 0:
        return False
    
    for x in unique_blocks:
        for y in x:
            if tag is y:
                return True
    
    return False

def mix_single_block(block):
    copied_list = [copy.copy(x) for x in block]
        
    index_occurance = [x for x in range(len(block))]
    
    for b in block:
        index_to_be_replaced = random.choice(index_occurance)
        index_occurance.remove(index_to_be_replaced)
        to_be_replaced = copied_list[index_to_be_replaced]
        
        b.replace_with(to_be_replaced)

def sensible_mix_single_block(block):
    if find_block_type(block) in ["div", "tr", "table"]:
        pad_len = len(block) // 4
        copied_list = [copy.copy(x) for x in block]
        
        index_occurance = [x for x in range(pad_len+1, len(block) - pad_len+1)]
        
        for b in block[pad_len:-1*pad_len]:
            index_to_be_replaced = random.choice(index_occurance)
            index_occurance.remove(index_to_be_replaced)
            to_be_replaced = copied_list[index_to_be_replaced-1]
            
            b.replace_with(to_be_replaced)
        return
    
    mix_single_block(block)

def is_one_kind(siblings):
    base_tag = siblings[0].name
    
    for tag in siblings:
        if tag.name != base_tag:
            return False
    
    return True

def find_block_type(block):
    return block[0].name
      
def mixer(soup, tag_name, sensible = False):
    unique_blocks = []
    tags = soup(tag_name)
    
    for tag in tags:
        
        if belongs_to_previous(tag, unique_blocks):
            continue
        
        next_siblings = tag.find_next_siblings(tag_name)
        prev_siblings = tag.find_previous_siblings(tag_name)
        block = prev_siblings + [tag] + next_siblings
        
        if len(block) < 3 or not is_one_kind(block):
            continue
        
        unique_blocks.append(block)
        
    unique_blocks.reverse()
        
    
    for block in unique_blocks:
        if sensible:
            sensible_mix_single_block(block)
        else:
            mix_single_block(block)
        
    print([len(x) for x in unique_blocks])
    
    return soup

def template_layout_randomizer(filename,output_path ,density = "soft"):
    
    with open(filename, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    sensible = False
    for x in range(10):
        if x == 5:
            sensible = True
        
        soup = mixer(soup, "table", sensible)
        soup = mixer(soup, "tr", sensible)
        soup = mixer(soup, "div", sensible)
        #soup = mixer(soup, "td")
        
        if density == "hard":
            soup = mixer(soup, "a", sensible)
            soup = mixer(soup, "p", sensible)
            soup = mixer(soup, "li", sensible)
        

        with open(output_path+f"/randomized_{x}.html", 'w', encoding='utf-8') as file:
            file.write(str(soup))

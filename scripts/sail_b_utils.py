import os, sys
from utils import *


# constants
SAIL_B_PIVOT_LEVEL = 24
HIGHTBIT = 2147483648       # bin : 10000000000000000000000000000000 , 32th bit is up
MAX_INIT_LEVEL = 24

class FibTree():
    """ Class for the Node """

    def __init__(self, parent = None, next_hop = None, level = 0, is_solid = False, is_pushed = False):

        self.parent = parent
        self.lchild = None
        self.rchild = None
        self.next_hop = next_hop
        self.level = level
        self.is_solid = is_solid
        self.is_pushed = is_pushed
        self.chunk_ID = -1

    def isLeaf(self):

        if self.lchild == None and self.rchild == None:
            return True
        else: 
            return False

    def initialize(self):

        return





class CFib():

    """ Class of the general algorithm """

    def __init__(self):
        
        self.root = FibTree()
        self.root.is_solid = True
        self.root.next_hop = 0 # default
        self.root.level = 0

        self.node_cnt = 0
        self.chunk_ID_nums = 0
        self.chunk_ID_map = []
        self.chunk_ID_lvl_origin = []


        self.bitmaps = {}
        self.next_hops = {}

        for i in range(25):
            self.bitmaps[i] = [0] * (2**i)
            self.next_hops[i] = [0] * (2**i)

        # set defaults
        self.bitmaps[0] = [1]
        self.next_hops[0] = [0]


    def subTrieLevelPushing(self, node : FibTree, default_port, port_origin_level):

        """ push the next hop to level 24 to non-existing nodes so far """

        # if the level is shallow, create new children nodes
        if node.level < 24: 
            
            # if node didn't exist yet, push the next hop data to it
            if node.lchild == None:

                lnode = FibTree(parent = node, next_hop=default_port, level = node.level + 1, is_pushed=True)
                node.lchild = lnode
                self.subTrieLevelPushing(node.lchild, default_port, port_origin_level)
            else:
                # if the node exists, but was pushed, push down the more relevant next hop
                if node.lchild.is_pushed == True:
                    node.lchild.next_hop = default_port
                    
                    # push further
                    self.subTrieLevelPushing(node.lchild, default_port, port_origin_level)


            if node.rchild == None:
                rnode = FibTree(parent = node, next_hop=default_port, level = node.level + 1, is_pushed=True)
                node.rchild = rnode
                self.subTrieLevelPushing(node.rchild, default_port, port_origin_level)
            else:
                # if the node exists, but was pushed, push down the more relevant next hop
                if node.rchild.is_pushed == True:
                    node.rchild.next_hop = default_port
                    
                    # push further
                    self.subTrieLevelPushing(node.rchild, default_port, port_origin_level)


        elif node.level == 24:

            # update the chunk ID table if exists
            if node.chunk_ID != -1:

                # check if the level of the pushed next port is lower than the level of the currently pushed node
                for bit in self.chunk_ID_map[(node.chunk_ID * 256) : ((node.chunk_ID+1) * 256)]:
                    if self.chunk_ID_lvl_origin[bit] < port_origin_level:
                        self.chunk_ID_lvl_origin[bit] = port_origin_level
                        self.chunk_ID_map[bit] = default_port
        else:                
            return


    def find_solid_ancestor(self, node):
        # recursion

        if node.is_solid == True:
            return node.level, node.next_hop
        else:
            level, next_hop = self.find_solid_ancestor(node.parent)
            return level, next_hop

                


    def update(self, insertPort, insert_C, plen):
        """ update the tree with new routing line """

        insertNode = self.root

        # 0. find the location of the current node
        for curr_level in range(plen):

            if insert_C[curr_level] == 1:
                # go right

                # if the node doesn't exist, create it 
                if insertNode.rchild == None:
                    rnode = FibTree(parent = insertNode, next_hop=-1, level = insertNode.level + 1)
                    insertNode.rchild = rnode
                    self.node_cnt += 1

                insertNode = insertNode.rchild

            else:
                # go left

                # if the node doesn't exist, create it 
                if insertNode.lchild == None:
                    lnode = FibTree(parent = insertNode, next_hop=-1, level = insertNode.level + 1)
                    insertNode.lchild = lnode
                    self.node_cnt += 1

                insertNode = insertNode.lchild

        
            # if the level of new node is bigger than 24, mark in bitmap of level 24
            # and create a new chunk ID

            if insertNode.level == 25:

                # check if the parent has chunk ID
                # if it does have, no need to add
                
                if insertNode.parent.chunk_ID == -1:
                    # create new chunk

                    binary_loc = insert_C[0:24]
                    binary_loc_str = ''.join(map(str, binary_loc))
                    dec_loc = int(binary_loc_str, 2)                    

                    self.bitmaps[24][dec_loc] = 1
                    new_chunk_ID = self.chunk_ID_nums
                    self.chunk_ID_nums += 1
                    self.next_hops[24][dec_loc] = -new_chunk_ID # negative
                    insertNode.parent.chunk_ID = new_chunk_ID

                    # find the first solid ancestor to get the port data to push down
                    anc_level, anc_port = self.find_solid_ancestor(insertNode)

                    # push all the ancestor data to this new chunk
                    self.chunk_ID_map.extend([anc_port]*256)
                    self.chunk_ID_lvl_origin.extend([anc_level]*256)

                    

             

        # 1. update the data for the current node
        insertNode.is_solid = True
        insertNode.is_pushed = False
        insertNode.next_hop = insertPort

        # 2. update the bitmap and Next Hop for levels 0-24
        if insertNode.level <= 24:

            binary_loc = insert_C[0:plen]
            binary_loc_str = ''.join(map(str, binary_loc))
            dec_loc = int(binary_loc_str, 2)

            self.bitmaps[insertNode.level][dec_loc] = 1
            self.next_hops[insertNode.level][dec_loc] = insertPort

            # 3. push the next hop info down the tree until level 24
            # and update the Lower Chunk arrays if the level of the originating Port was higher than current
            self.subTrieLevelPushing(insertNode, insertPort, insertNode.level)

        # 4. if the level is > 24, we have to update the chunk ID memory if needed

        if insertNode.level > 24:

            chunk_bin_loc = insert_C[24:plen]
            chunk_bin_loc_str = ''.join(map(str, chunk_bin_loc))
            dec_loc = int(chunk_bin_loc_str, 2)

            # fill up to the length of 8 to find the min and max location to update in the chunk
            chunk_bin_loc_min = dec_loc << (32 - insertNode.level)
            chunk_bin_loc_max = chunk_bin_loc_min + (2**(32 - insertNode.level))-1

            # for each entry in the chunk array, check the level which pushed it
            # if it's smaller than relevant bits, update the next hop array

            # find the chunk_ID number
            chunk_ID_binary_loc = insert_C[0:24]
            chunk_ID_binary_loc_str = ''.join(map(str, chunk_ID_binary_loc))
            chunk_ID_dec_loc = int(chunk_ID_binary_loc_str, 2) 

            chunk_ID = -self.next_hops[24][chunk_ID_dec_loc] # negative -> positive

            for chunk_bit in range(chunk_bin_loc_min, chunk_bin_loc_max):

                if self.chunk_ID_lvl_origin[(chunk_ID * 256) + chunk_bit] < curr_level:
                    self.chunk_ID_lvl_origin[(chunk_ID * 256) + chunk_bit] = curr_level
                    self.chunk_ID_map[(chunk_ID * 256) + chunk_bit] = insertPort

        return 



    def build_fib_from_file(self, fib_filepath, print_every : int):

        # 1. initialize empty tree up to lvl 24
        # self.initialize()

        # 2. read the file

        cnt = 0

        with open(fib_filepath) as fd:

            for line in fd:

                cnt += 1

                # 2.1 get the IP, prefixlen and next hop from the line
                ip, plen, nhop = parse_line(line)

                # 2.1 create the vector of directions which tells if to turn right or left
                insert_B = [0]*32

                for yi in range(plen):
                    if  ((ip << yi) & HIGHTBIT) == HIGHTBIT:
                        insert_B[yi] = 1
                    else:
                        insert_B[yi]= 0

                self.update(nhop, insert_B, plen)

                # print("here")

                if cnt % print_every == 0:
                    print("=" * 50 + "\n")
                    print(f"Analyzed {cnt} rows\n")
                    self.print_statistics()


    def print_statistics(self):

        print(f"STATISTICS:")
        print(f"\tTotal nodes created: {self.node_cnt}")
        print(f"\tbitmaps population wrt levels:")
        for key in self.bitmaps.keys():
            level_sum = sum(self.bitmaps[key])
            print(f"\t\tOn level {key} : {level_sum}")
        print(f"Number of chunks: {self.chunk_ID_nums}")

        next_hops_24 = list(set(self.next_hops[24]))
        chunk_id_next_hops_24 = [i for i in next_hops_24 if i <= 0]

        print(f"Number of chunk id next hops at lvl 24: {len(chunk_id_next_hops_24)}")
        

    def create_bitmaps(self, output_bitmap_fold):

        # dump the bitmaps
        print("-" * 50 + "\n\n")
        print(f"Dumping bitmaps:")
        bitmaps_output_f = os.path.abspath(os.path.join(output_bitmap_fold, 'bitmaps'))
        os.makedirs(bitmaps_output_f, exist_ok=True)
        for key in self.bitmaps.keys():
            print(f"Bitmap #{key}")
            with open(os.path.join(bitmaps_output_f, f"bitmap_{key}.txt"), 'w') as f:
                for item in self.bitmaps[key]:
                    f.write(f"{item}\n")

        # dump the next hop arrays
        print("-" * 50 + "\n\n")
        print(f"Dumping next hop arrays:")        
        next_hops_output_f = os.path.abspath(os.path.join(output_bitmap_fold, 'next_hops'))
        os.makedirs(next_hops_output_f, exist_ok=True)
        for key in self.next_hops.keys():
            print(f"Array #{key}")
            with open(os.path.join(next_hops_output_f, f"next_hop_{key}.txt"), 'w') as f:
                for item in self.next_hops[key]:
                    f.write(f"{item}\n")


        # dump the chunk ID memories



        print("here")
        return
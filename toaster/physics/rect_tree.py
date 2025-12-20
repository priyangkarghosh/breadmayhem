from __future__ import annotations
from typing import Optional, Callable
from dataclasses import dataclass, field
from pygame import gfxdraw, Rect, Surface
from toaster.misc.extra import rect_area
from toaster.registry.registry import Registry
from toaster.physics.physics_handler import PhysicsRect

OVERLAP_ERROR = (8, 8)


@dataclass
class TreeNode:
    value: Optional[PhysicsRect] = None
    fattened_rect: Optional[Rect] = field(default=None, init=False)

    left: Optional[TreeNode] = None
    right: Optional[TreeNode] = None
    parent: Optional[TreeNode] = None

    height: int = 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TreeNode):
            return self.value == other.value
        return False

    @property
    def leaf(self) -> bool:
        return self.left is None


class RectTree:
    def __init__(self, fat: tuple[int, int] = (6, 6)):
        self.root: Optional[TreeNode] = None
        self.fat: tuple[int, int] = fat

    def insert_leaf(self, physics_rect: PhysicsRect) -> None:
        assert physics_rect.rect
        
        if not self.root:
            self.root = TreeNode(value=physics_rect)
            self.root.fattened_rect = physics_rect.rect.inflate(self.fat)
            return

        temp: TreeNode = self.root
        while not temp.leaf:
            assert temp.left is not None and temp.right is not None

            # areas of the different nodes
            left_area = rect_area(temp.left.value.rect) # type: ignore
            right_area = rect_area(temp.right.value.rect) # type: ignore
            center_area = rect_area(temp.value.rect) # type: ignore

            # areas of the different rect unions
            left_union_area = rect_area(temp.left.value.rect.union(physics_rect.rect)) # type: ignore
            right_union_area = rect_area(temp.right.value.rect.union(physics_rect.rect)) # type: ignore
            center_union_area = rect_area(temp.value.rect.union(physics_rect.rect)) # type: ignore

            # calculate costs to create additional branches
            branch_cost = 2 * center_union_area
            min_push_cost = 2 * (center_union_area - center_area)

            left_cost = min_push_cost + left_union_area
            if not temp.left.leaf:
                left_cost -= left_area

            right_cost = min_push_cost + right_union_area
            if not temp.right.leaf:
                right_cost -= right_area

            # create a new branch here if it costs the least
            if branch_cost < left_cost and branch_cost < right_cost:
                break

            # traverse left or right based on the cheaper option
            if left_cost < right_cost: temp = temp.left
            else: temp = temp.right

        # create the new branch
        sibling = temp
        old_parent = sibling.parent

        leaf = TreeNode(value=physics_rect)
        leaf.fattened_rect = physics_rect.rect.inflate(self.fat)

        # the new parent will be the union of the leaf and sibling
        new_parent = TreeNode(
            value=PhysicsRect(phys_rect=leaf.value.rect.union(sibling.value.rect)), # type: ignore
            parent=old_parent,
            left=sibling,
            right=leaf,
            height=temp.height + 1
        )

        # make sure the parent of the sibling and leaf is updated
        sibling.parent = leaf.parent = new_parent

        # update the references
        if not old_parent:
            self.root = new_parent
        elif old_parent.left == sibling:
            old_parent.left = new_parent
        else:
            old_parent.right = new_parent

        # fix the tree
        self.preen(leaf.parent)

    def remove_leaf(self, leaf: TreeNode) -> None:
        if not leaf.leaf:
            return

        if leaf == self.root:
            self.root = None
            return

        parent = leaf.parent
        assert parent is not None
        
        grandparent = parent.parent
        sibling = parent.left if parent.right == leaf else parent.right
        assert sibling is not None

        if grandparent:
            if grandparent.left == parent:
                grandparent.left = sibling
            else:
                grandparent.right = sibling
            sibling.parent = grandparent
            self.preen(grandparent)
        else:
            self.root = sibling
            sibling.parent = None
        leaf.parent = None

    def preen(self, node: Optional[TreeNode]) -> None:
        while node:
            node = self.balance_node(node)
            assert node.left is not None and node.right is not None
            node.height = 1 + max(node.left.height, node.right.height)
            node.value = PhysicsRect(phys_rect=node.left.value.rect.union(node.right.value.rect)) # type: ignore
            node = node.parent

    def fit_leaf(self, leaf: TreeNode) -> None:
        if leaf.parent is None:
            return

        # inflate the parent to check if it's still within bounds
        if leaf.fattened_rect.contains(leaf.value.rect): # type: ignore
            return

        self.remove_leaf(leaf)
        self.insert_leaf(leaf.value) # type: ignore

    def balance_node(self, node: TreeNode) -> TreeNode:
        if node.leaf or node.height < 2:
            return node

        assert node.left and node.right
        balance = node.right.height - node.left.height
        if balance > 1: return self.balance_right(node)
        elif balance < -1: return self.balance_left(node)
        return node

    def balance_right(self, node: TreeNode) -> TreeNode:
        assert node.left is not None and node.right is not None
        left_child = node.left
        right_child = node.right

        assert right_child.left is not None and right_child.right is not None
        left_grandchild = right_child.left
        right_grandchild = right_child.right

        # set the current node as the new left grandchild
        right_child.left = node
        right_child.parent = node.parent
        node.parent = right_child

        # shift the child
        grandfather = right_child.parent
        if grandfather:
            if grandfather.left == node:
                grandfather.left = right_child
            else:
                grandfather.right = right_child
        else:
            self.root = right_child

        # swap the children
        if left_grandchild.height > right_grandchild.height:
            right_child.right = left_grandchild
            node.right = right_grandchild
            right_grandchild.parent = node

            node.value = PhysicsRect(phys_rect=left_child.value.rect.union(right_grandchild.value.rect)) # type: ignore
            right_child.value = PhysicsRect(phys_rect=node.value.rect.union(left_grandchild.value.rect)) # type: ignore

            node.height = 1 + max(left_child.height, right_grandchild.height)
            right_child.height = 1 + max(node.height, left_grandchild.height)
        else:
            right_child.right = right_grandchild
            node.right = left_grandchild
            left_grandchild.parent = node

            node.value = PhysicsRect(phys_rect=left_child.value.rect.union(left_grandchild.value.rect)) # type: ignore
            right_child.value = PhysicsRect(phys_rect=node.value.rect.union(right_grandchild.value.rect)) # type: ignore

            node.height = 1 + max(left_child.height, left_grandchild.height)
            right_child.height = 1 + max(node.height, right_grandchild.height)

        # return the new balanced node
        return right_child

    def balance_left(self, node: TreeNode) -> TreeNode:
        assert node.left is not None and node.right is not None
        left_child = node.left
        right_child = node.right

        assert left_child.left is not None and left_child.right is not None
        left_grandchild = left_child.left
        right_grandchild = left_child.right

        # set the current node as the new left grandchild
        left_child.left = node
        left_child.parent = node.parent
        node.parent = left_child

        # shift the child
        grandfather = left_child.parent
        if grandfather:
            if grandfather.left == node:
                grandfather.left = left_child
            else:
                grandfather.right = left_child
        else:
            self.root = left_child

        # swap the children
        if left_grandchild.height > right_grandchild.height:
            left_child.right = left_grandchild
            node.left = right_grandchild
            right_grandchild.parent = node

            node.value = PhysicsRect(phys_rect=right_child.value.rect.union(right_grandchild.value.rect)) # type: ignore
            left_child.value = PhysicsRect(phys_rect=node.value.rect.union(left_grandchild.value.rect)) # type: ignore

            node.height = 1 + max(right_child.height, right_grandchild.height)
            left_child.height = 1 + max(node.height, left_grandchild.height)
        else:
            left_child.right = right_grandchild
            node.left = left_grandchild
            left_grandchild.parent = node

            node.value = PhysicsRect(phys_rect=right_child.value.rect.union(left_grandchild.value.rect)) # type: ignore
            left_child.value = PhysicsRect(phys_rect=node.value.rect.union(right_grandchild.value.rect)) # type: ignore

            node.height = 1 + max(right_child.height, left_grandchild.height)
            left_child.height = 1 + max(node.height, right_grandchild.height)

        # return the new balanced node
        return left_child

    def print_tree(self, node: Optional[TreeNode] = None, level: int = 0) -> None:
        if node is not None:
            self.print_tree(node.left, level + 1)
            print(' ' * 6 * level + '-> ' + str(level))
            self.print_tree(node.right, level + 1)

    def get_overlaps(self, phys_rect: PhysicsRect) -> list[PhysicsRect]:
        if not self.root:
            return []

        overlaps = []
        stack = [self.root]
        check_rect = phys_rect.rect.inflate(OVERLAP_ERROR) # type: ignore

        while stack:
            subtree = stack.pop()
            if subtree.value is phys_rect:
                continue
            if subtree.value.rect.colliderect(check_rect): # type: ignore
                if subtree.leaf:
                    overlaps.append(subtree.value)
                else:
                    stack.append(subtree.left) # type: ignore
                    stack.append(subtree.right) # type: ignore
        return overlaps

    def update(self) -> None:
        if not self.root:
            return
            
        stack = [self.root]
        while stack:
            subtree = stack.pop()
            if not subtree:
                continue

            if subtree.leaf:
                self.fit_leaf(subtree)
            else:
                stack.append(subtree.left) # type: ignore
                stack.append(subtree.right) # type: ignore

    def traverse(self, func: Optional[Callable[[TreeNode], None]] = None) -> None:
        if not self.root:
            return
            
        stack = [self.root]
        while stack:
            subtree = stack.pop()
            if not subtree:
                continue

            if func:
                func(subtree)
            if not subtree.leaf:
                stack.append(subtree.left) # type: ignore
                stack.append(subtree.right) # type: ignore

    def render(self, surf: Surface, colour: tuple[int, int, int, int], 
               subtree: Optional[TreeNode] = None) -> None:
        if subtree is None:
            self.traverse(func=lambda x: self.render(surf, colour, x))
            return

        pos = Registry.instance()['camera'].world_to_camera(subtree.value.rect.topleft) # type: ignore
        gfxdraw.box(surf, (*pos, *subtree.value.rect.size), colour) # type: ignore

    def clear(self) -> None:
        self.root = None

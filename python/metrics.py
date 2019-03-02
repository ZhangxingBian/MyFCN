import torch
from torch.autograd import Function, Variable
def iou(pred, target,n_class):
    ious = []
    for cls in range(n_class):
        pred_inds = pred == cls+1
        target_inds = target == cls+1
        intersection = torch.sum(pred_inds[target_inds])
        union = torch.sum(pred_inds) + torch.sum(target_inds) - intersection
        if union == 0:
            ious.append(torch.float('nan'))  # if there is no ground truth, do not include in evaluation
        else:
            ious.append(intersection.float()/torch.max(union.float(), torch.tensor(1.).float().cuda()))
    return ious


def pixel_acc(pred, target):
    correct = (pred == target).sum()
    total   = (target == target).sum()
    return correct / total



class DiceCoeff(Function):
    """Dice coeff for individual examples"""

    def forward(self, input, target):
        self.save_for_backward(input, target)
        eps = 0.0001
        # print(input.type(),target.type())
        self.inter = torch.dot(input.view(-1),target.view(-1))
        self.union = torch.sum(input) + torch.sum(target) + eps

        t = (2 * self.inter + eps) / self.union
        return t

    # This function has only a single output, so it gets only one gradient
    def backward(self, grad_output):

        input, target = self.saved_variables
        grad_input = grad_target = None

        if self.needs_input_grad[0]:
            grad_input = grad_output * 2 * (target * self.union - self.inter) \
                         / (self.union * self.union)
        if self.needs_input_grad[1]:
            grad_target = None

        return grad_input, grad_target


def dice_coeff(input, target):
    """Dice coeff for batches"""
    if input.is_cuda:
        s = torch.FloatTensor(1).cuda().zero_()
    else:
        s = torch.FloatTensor(1).zero_()

    for i, c in enumerate(zip(input, target)):
        s = s + DiceCoeff().forward(c[0], c[1])

    return s / (i + 1)

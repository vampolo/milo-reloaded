function [recomList] = onLineRecom_ASYSVD (userProfile, model,param)
%userProfile = vector with ratings of a single user
%model = model created with createModel function 
% model:    model.mu --> average rating
%           model.bu --> vector of the average rating for each user
%           model.bi --> vector of the average rating for each item
%           model.q 
%           model.x
%           model.y
%           [model.p]
%           [model.z]
%param.postProcessingFunction = handle of post-processing function (e.g., business-rules)
%param.userToTest

    try
        mu=model.mu;
%XXX        bu=model.bu;
        bi=model.bi;
        x=model.x;
        y=model.y;
        q=model.q;
        ls=size(x,1);
%XXX        user=param.userToTest;

%XXXXXXXXXXXXXXXXXXXXXXXXXXXXX ->>>>
    catch e
        display e
        error ('missing some model field');
    end
    try
        bu=model.bu(param.userToTest);
    catch e
        bu=0;
    end
%XXXXXXXXXXXXXXXXXXXXXXXXXXXXX <<<<-

       
    pu=zeros(ls,1);
    ratedItems = find(userProfile);
    numRatedItems = length(ratedItems);
    if (numRatedItems==0) 
       warning('empty user profile!');
    end        
    for i=1:numRatedItems
        item=ratedItems(i);
%XXX        pu = pu +  (userProfile(item) - (mu+bu(user)+bi(item)))*x(:,item);
%XXXXXXXXXXXXXXXXXXXXXXXXXXXXX ->>>>
        pu = pu +  (userProfile(item) - (mu+bu+bi(item)))*x(:,item);
%XXXXXXXXXXXXXXXXXXXXXXXXXXXXX <<<<-
        pu = pu +  y(:,item);
    end
    pu = pu / sqrt(numRatedItems);   
    
    recomList = mu + bu(user) + bi + q'*pu; %r_hat_ui = mu + bu(u) + bi(item) + q(:,item)'*pu; 
        

    
    if (nargin>=3)
        if(isfield(param,'postProcessingFunction'))
            if(strcmp(class(param.postProcessingFunction),'function_handle'))
                recomList=feval(param.postProcessingFunction,recomList,param);
            end
        end
    end
end
